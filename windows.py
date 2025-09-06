#!/usr/bin/env python3
import os
import subprocess
import sys
import shlex
import re
from platform_base import PlatformHelper


class WindowsHelper(PlatformHelper):
    """
    Platform helper for Windows systems:
    Handles configuration and data directories,
    browser detection, and browser launching.
    """

    def __init__(self):
        # Initialize browser map with detected browsers
        self.browser_map = self._detect_browsers()
        self.config = None  # Assigned externally if needed
        self.aliases = {}

    def is_sandboxed_windows(self):
        """
        Detect if running in Windows Store sandbox (App Container).
        """
        exec_path = sys.executable.lower()
        return (
            "windowsapps" in exec_path
            and "pythonsoftwarefoundation.python" in exec_path
        )

    def get_platform_dirs(self):
        """
        Return tuple of (config_dir, data_dir) paths appropriate for Windows.
        Uses platformdirs library for standard locations, except when sandboxed.
        """
        from platformdirs import user_config_dir, user_data_dir

        if self.is_sandboxed_windows():
            base_path = os.path.expandvars(
                r"%LOCALAPPDATA%\Packages\PythonSoftwareFoundation.Python_8wekyb3d8bbwe"
                r"\LocalCache\Roaming\dmnmsc\kwebsearch"
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
        """
        Open the given configuration file using Windows default file handler.
        """
        if verbose:
            print(f"Opening configuration file at: {path}")
        os.startfile(path)

    def _detect_browsers(self):
        """
        Detect installed browsers using the 'browsers' package.
        Returns a dict mapping lowercase browser names to their executable paths.
        Falls back to extra browsers from config if package missing.
        """
        try:
            import browsers
        except ImportError:
            # Fallback to extra browsers from config if available
            if hasattr(self, 'config') and self.config and hasattr(self.config, 'get_extra_browsers'):
                ext = self.config.get_extra_browsers()
                return {b.lower(): b for b in ext}
            return {}

        browsers_map = {}
        for b in browsers.browsers():
            name = (
                b.get("browser_type")
                or b.get("display_name")
                or b.get("name")
            )
            path = b.get("path") or b.get("location")

            if name and path and os.path.isfile(path):
                browsers_map[name.lower()] = path

        # Add extra browsers set in config, avoid duplicates
        if hasattr(self, "config") and self.config:
            try:
                extra = self.config.get_extra_browsers()
                for ex in extra:
                    ex_lower = ex.lower()
                    if ex_lower not in browsers_map:
                        browsers_map[ex_lower] = ex
            except Exception:
                pass

        return browsers_map

    def detect_available_browsers(self):
        """
        Return sorted list of detected browser names.
        """
        return sorted(self.browser_map.keys())

    def is_browser_name_safe(self, browser_str):
        """
        Validate that the browser executable name consists of safe characters.
        """
        pattern = r"^[a-zA-Z0-9_.+\-]+(\.exe)?$"
        return bool(re.match(pattern, browser_str))

    def import_extra_browsers(self, use_deep_scan=False):
        """
        Import extra browsers, optionally with a deep scan using 'installed_browsers' package.
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

    def get_default_browser_command(self, default_browser_name):
        """
        Given a default_browser string from config, resolve it to a (executable_path, args) tuple.
        Supports short names by looking them up in the browser_map.
        """
        parts = shlex.split(default_browser_name)
        exec_path_or_name = parts[0]
        args = parts[1:]

        exec_key = exec_path_or_name.lower()
        resolved_exec_path = self.browser_map.get(exec_key, exec_path_or_name)

        return resolved_exec_path, args

    def launch_browser(self, cmd_list, verbose=False):
        """
        Launches browser or executable defined by cmd_list.
        Resolves known short names to absolute paths and temporarily updates PATH.
        Uses shell=False for absolute paths, shell=True for others.
        """
        if not cmd_list:
            if verbose:
                print("[Windows] No command specified for launching browser.")
            return False

        exec_path = cmd_list[0]
        args = cmd_list[1:]
        exec_path_lower = exec_path.lower()

        # Resolve short name to absolute path if possible
        path_to_exec = self.browser_map.get(exec_path_lower, exec_path)

        # Temporarily add executable directory to PATH to help subprocess find it
        browser_dir = os.path.dirname(path_to_exec)
        if browser_dir:
            current_path = os.environ.get("PATH", "")
            paths_lower = [p.lower() for p in current_path.split(os.pathsep) if p]
            if browser_dir.lower() not in paths_lower:
                os.environ["PATH"] = browser_dir + os.pathsep + current_path
                if verbose:
                    print(f"[Windows] Temporarily added '{browser_dir}' to PATH")

        final_cmd = [path_to_exec] + args

        try:
            is_abs_path = os.path.isabs(path_to_exec) and os.path.isfile(path_to_exec)
            if verbose:
                print(f"[Windows] Launching browser command: {final_cmd} | is_abs_path: {is_abs_path}")

            if is_abs_path:
                subprocess.Popen(final_cmd, shell=False)
            else:
                # Compose command string with quoting for shell use
                cmd_str = " ".join(f'"{arg}"' if " " in arg else arg for arg in final_cmd)
                if verbose:
                    print(f"[Windows] Launching browser with shell=True command: {cmd_str}")
                subprocess.Popen(cmd_str, shell=True)
            return True
        except Exception as e:
            if verbose:
                print(f"[Windows] Error launching browser: {e}")
            return False

    def launch_url(self, url, verbose=False):
        """
        Launch specified URL using default browser configured in kwebsearch.conf.
        Uses 'browsers.launch' when available, falls back to manual launching or system default.
        """
        try:
            import browsers
        except ImportError:
            browsers = None
            if verbose:
                print("[Windows] 'browsers' module not found, falling back")

        default_browser_str = self.read_default_browser_from_config()

        if not default_browser_str:
            if verbose:
                print("[Windows] No default_browser configured, using system default browser")
            subprocess.Popen(f'start "" "{url}"', shell=True)
            return

        parts = shlex.split(default_browser_str)
        browser_name = parts[0].lower()
        args = parts[1:]

        if browsers:
            try:
                if verbose:
                    print(f"[Windows] Launching URL '{url}' using browsers.launch({browser_name}) with args {args}")
                browsers.launch(browser_name, args=args, url=url)
                return
            except Exception as e:
                if verbose:
                    print(f"[Windows] browsers.launch failed: {e}")

        # Fallback to manual launch
        exec_path, args_resolved = self.get_default_browser_command(default_browser_str)
        cmd_list = [exec_path] + args_resolved + [url]

        if verbose:
            print(f"[Windows] Fallback launching URL with command list: {cmd_list}")

        try:
            subprocess.Popen(cmd_list)
        except Exception as e:
            if verbose:
                print(f"[Windows] Error launching URL by subprocess: {e}")
            subprocess.Popen(f'start "" "{url}"', shell=True)

    def read_default_browser_from_config(self):
        """
        Read the 'default_browser' setting from the kwebsearch.conf file.
        """
        if not self.config:
            return ""

        config_dir, _ = self.get_platform_dirs()
        conf_path = os.path.join(config_dir, "kwebsearch.conf")

        if not os.path.exists(conf_path):
            return ""

        with open(conf_path, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if line.startswith("default_browser="):
                    return line.split("=", 1)[1].strip().strip('"')
        return ""

    def launch_default_system_url(self, url, verbose=False):
        """
        Launch URL using the system’s default browser via Windows 'start' command.
        """
        if verbose:
            print(f"[Windows] Launching system default browser with URL: {url}")
        subprocess.Popen(f'start "" "{url}"', shell=True)

    def launch_alias_command(self, command_line, verbose=False):
        parts = shlex.split(command_line)
        if not parts:
            if verbose:
                print("[Windows] Alias command empty")
            return False

        exec_name = parts[0].lower()
        args = parts[1:]

        # Resolve exec path
        exec_path = self.browser_map.get(exec_name, exec_name)

        cmd_list = [exec_path] + args

        if verbose:
            print(f"[Windows] Launching alias command list: {cmd_list}")

        try:
            subprocess.Popen(cmd_list, shell=False)
            return True
        except Exception as e:
            if verbose:
                print(f"[Windows] Error launching alias command as list: {e}")
            # Fallback con start shell=True
            try:
                start_cmd = f'start "" {command_line}'
                if verbose:
                    print(f"[Windows] Fallback launching alias command with start: {start_cmd}")
                subprocess.Popen(start_cmd, shell=True)
                return True
            except Exception as e2:
                if verbose:
                    print(f"[Windows] Error launching alias command fallback with start: {e2}")
                return False
