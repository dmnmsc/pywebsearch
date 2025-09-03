#!/usr/bin/env python3
import os
import subprocess
import sys
import re
from platform_base import PlatformHelper

class WindowsHelper(PlatformHelper):
    """Platform helper for Windows systems:
    Handles config/data directories, browser detection, and browser launching."""

    def is_sandboxed_windows(self):
        """Detect whether Python is running in the Windows Store sandbox."""
        exec_path = sys.executable.lower()
        return (
            "windowsapps" in exec_path
            and "pythonsoftwarefoundation.python" in exec_path
        )

    def get_platform_dirs(self):
        """Get standard config and data directories for Windows."""
        from platformdirs import user_config_dir, user_data_dir
        if self.is_sandboxed_windows():
            base_path = os.path.expandvars(
                r"%LOCALAPPDATA%\Packages\PythonSoftwareFoundation.Python_8wekyb3d8bbwe\LocalCache\Roaming\dmnmsc\kwebsearch"
            )
            config_dir = base_path
            data_dir = os.path.join(base_path, "data")
        else:
            config_dir = user_config_dir(
                "kwebsearch", appauthor="dmnmsc", ensure_exists=True
            )
            data_dir = user_data_dir(
                "kwebsearch", appauthor="dmnmsc", ensure_exists=True
            )
        return config_dir, data_dir

    def open_config_file(self, path, verbose=False):
        """Open the configuration file using the default Windows handler."""
        if verbose:
            print(f"Opening configuration file at: {path}")
        os.startfile(path)

    def detect_available_browsers(self):
        """
        Detect installed browsers using installed_browsers. Also include any extra
        browsers added by the user and stored in configuration.
        Local import: Only loads installed_browsers if this function is used.
        """
        detected = set()
        try:
            import installed_browsers
            for browser in installed_browsers.browsers():
                name = browser.get("name")
                if name:
                    exe_name = name if name.endswith(".exe") else name + ".exe"
                    detected.add(exe_name.lower())
        except ImportError:
            print("[WindowsHelper] 'installed_browsers' not installed.")
            # Detected set stays empty
        # Merge extra browsers from config if available
        if hasattr(self, "config"):
            try:
                detected.update(self.config.get_extra_browsers())
            except Exception:
                pass
        return detected


    def is_browser_name_safe(self, browser_str):
        """Validate browser name to allow only safe executable names."""
        pattern = r"^[a-zA-Z0-9_.+\-]+(\.exe)?$"
        return bool(re.match(pattern, browser_str))

    def import_extra_browsers(self, use_deep_scan=False):
        """
        On-demand import of extra browsers.
        Uses 'browsers' library for fast detection by default,
        or optionally uses 'installed_browsers' for deep scan (local import) if requested.
        """
        manual_detected = self.detect_available_browsers()
        found = set()
        if use_deep_scan:
            try:
                import installed_browsers
            except ImportError:
                print("[WindowsHelper] 'installed_browsers' not installed.")
                return set()
            for browser in installed_browsers.browsers():
                exe = browser.get("name")
                if exe and self.is_browser_name_safe(exe):
                    exe_name = exe if exe.endswith(".exe") else exe + ".exe"
                    if exe_name.lower() not in manual_detected:
                        found.add(exe_name.lower())
        else:
            try:
                import browsers
            except ImportError:
                print("[WindowsHelper] 'browsers' module not installed.")
                return set()
            for browser in browsers.browsers():
                exe = (
                    browser.get("browser_type")
                    or browser.get("display_name")
                    or browser.get("name")
                )
                if exe and self.is_browser_name_safe(exe):
                    exe_name = exe if exe.endswith(".exe") else exe + ".exe"
                    if exe_name.lower() not in manual_detected:
                        found.add(exe_name.lower())
        return found

    def is_browser_available(self, browser_path, verbose=False):
        """
        Check if a particular browser executable is available and installed.
        Local import of installed_browsers for robustness.
        Also allows custom user-defined browser names specified in alias keys.
        """
        exe_name = os.path.basename(browser_path).lower()
        # Check normal installed_browsers detection
        try:
            import installed_browsers
        except ImportError:
            print("[WindowsHelper] 'installed_browsers' not installed.")
            return False
        available = exe_name in self.detect_available_browsers() and bool(
            installed_browsers.do_i_have_installed(exe_name.rstrip(".exe"))
        )
        if verbose:
            print(f"[WindowsHelper] Browser '{exe_name}' available: {available}")
        if available:
            return True
        # Check if browser name is defined in user-added aliases
        if hasattr(self, "aliases") and exe_name in self.aliases:
            if verbose:
                print(f"[WindowsHelper] Browser '{exe_name}' is defined in custom aliases.")
            return True
        if verbose:
            print(f"[WindowsHelper] Browser '{exe_name}' not found or not allowed.")
        return False

    def launch_browser(self, cmd_list, verbose=False):
        """Launch a browser process with the given command list."""
        browser = os.path.basename(cmd_list[0]).lower()
        if not self.is_browser_available(browser):
            if verbose:
                print(f"[Windows] Browser '{browser}' not found or not allowed.")
            return False
        try:
            if verbose:
                print(f"[Windows] Launching browser command: {' '.join(cmd_list)}")
            subprocess.Popen(cmd_list, shell=True)
            return True
        except Exception as e:
            if verbose:
                print(f"[Windows] Error launching browser: {e}")
            return False

    def get_default_browser_command(self, default_browser_name):
        """Get the path for the default browser, if available."""
        try:
            import installed_browsers
        except ImportError:
            print("[WindowsHelper] 'installed_browsers' not installed.")
            return default_browser_name
        default_name = default_browser_name.lower().rstrip(".exe")
        for browser in installed_browsers.browsers():
            name = browser.get("name", "").lower()
            if name == default_name or name.rstrip(".exe") == default_name:
                path = browser.get("location") or browser.get("path")
                if path and os.path.isfile(path):
                    return path
        return default_browser_name

    def launch_default_system_url(self, url, verbose=False):
        """Launch a URL using the default system browser (Windows 'start' command)."""
        if verbose:
            print(f"[Windows] Launching default system URL fallback with start: {url}")
        subprocess.Popen(f'start "" "{url}"', shell=True)

    def launch_alias_command(self, command_line, verbose=False):
        """Launch alias commands on Windows using cmd 'start' with proper quoting."""
        cmd_line = f'start "" {command_line}'
        if verbose:
            print(f"Launching Windows alias command: {cmd_line}")
        try:
            subprocess.Popen(cmd_line, shell=True)
            return True
        except Exception as e:
            if verbose:
                print(f"Error launching alias command: {e}")
            return False
