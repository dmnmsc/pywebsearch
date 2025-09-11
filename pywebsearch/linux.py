#!/usr/bin/env python3
import glob
import os
import shutil
import subprocess
from pywebsearch.platformbase import PlatformHelper
from PyQt6.QtGui import QIcon
import re


script_dir = os.path.dirname(os.path.abspath(__file__))

ICON_INSTALLED = "/usr/share/icons/hicolor/48x48/apps/pywebsearch.png"

ICON_LOCAL = os.path.join(script_dir, "resources", "pywebsearch.png")


def get_icon() -> QIcon:
    if os.path.exists(ICON_INSTALLED):
        return QIcon(ICON_INSTALLED)
    elif os.path.exists(ICON_LOCAL):
        return QIcon(ICON_LOCAL)
    else:
        return QIcon()


class LinuxHelper(PlatformHelper):
    """Platform helper for Linux systems to manage configuration directories,
    browser detection, and launching browsers or URLs."""

    def get_platform_dirs(self):
        """Get standard config and data directories for Linux."""
        from platformdirs import user_config_dir, user_data_dir
        config_dir = user_config_dir(
            "pywebsearch",
            appauthor="dmnmsc",
            ensure_exists=True,
        )
        data_dir = user_data_dir("pywebsearch", appauthor="dmnmsc", ensure_exists=True)
        return config_dir, data_dir

    def open_config_file(self, path, verbose=False):
        """Open the configuration file using the default system handler."""
        if verbose:
            subprocess.run(["xdg-open", path])
        else:
            subprocess.Popen(
                ["xdg-open", path],
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
                start_new_session=True,
            )

    def detect_available_browsers(self):
        """Detect commonly used browser executables in PATH and add any user-defined extra browsers from configuration."""
        browser_patterns = [
            "firefox*",
            "chromium*",
            "google-chrome*",
            "brave*",
            "opera*",
            "vivaldi*",
            "microsoft-edge*",
        ]
        detected = set()
        for pattern in browser_patterns:
            for path_entry in os.environ.get("PATH", "").split(os.pathsep):
                for match in glob.glob(os.path.join(path_entry, pattern)):
                    exe = os.path.basename(match)
                    if os.access(match, os.X_OK):
                        detected.add(exe)
        # Detect common text-based browsers
        for text_browser in ["lynx", "w3m", "links"]:
            if shutil.which(text_browser):
                detected.add(text_browser)
        # Add user-imported browsers from config if available
        if hasattr(self, "config"):
            try:
                detected.update(self.config.get_extra_browsers())
            except Exception:
                pass
        return detected

    def is_browser_available(self, browser_name):
        # If browser_name is detected normally
        if browser_name in self.detect_available_browsers() and shutil.which(browser_name) is not None:
            return True
        # If user defined it explicitly in an alias, allow (user responsibility)
        if hasattr(self, "aliases") and browser_name in self.aliases:
            return True
        # Otherwise, block
        return False

    def launch_browser(self, cmd_list, verbose=False):
        """Launch a browser process with given command list."""
        browser = os.path.basename(cmd_list[0])
        if not self.is_browser_available(browser):
            if verbose:
                print(f"[Linux] Browser '{browser}' not found or not allowed.")
            return False
        try:
            if verbose:
                print(f"[Linux] Launching browser command: {' '.join(cmd_list)}")
            subprocess.Popen(cmd_list)
            return True
        except Exception as e:
            if verbose:
                print(f"[Linux] Error launching browser: {e}")
            return False

    def is_browser_name_safe(self, browser_str):
        """
        Validate browser name to allow only safe executable names.
        """
        import re
        pattern = r"^[a-zA-Z0-9_.+\-]+$"
        return bool(re.match(pattern, browser_str))

    def launch_default_system_url(self, url, verbose=False):
        """Fallback launcher using xdg-open for URLs."""
        if verbose:
            print(f"[Linux] Launching default system URL fallback with xdg-open: {url}")
        subprocess.Popen(
            ["xdg-open", url],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            start_new_session=True,
        )

    def import_extra_browsers(self):
        """On-demand import and detection of extra browsers via the 'browsers' library.

        This method imports the 'browsers' module only when called to avoid
        performance cost during startup. Returns a set of executable names
        that are detected by 'browsers' but not by the manual detect_available_browsers method.

        Returns:
            Set[str]: Names of extra browser executables detected.
        """
        try:
            import browsers  # Import only when needed to avoid startup overhead.
        except ImportError:
            print("[LinuxHelper] 'browsers' module not installed.")
            return set()

        detected_manual = self.detect_available_browsers()

        def is_browser_name_safe(browser_str):
            """Validate browser name to allow only safe executable names."""
            pattern = r"^[a-zA-Z0-9_.+\-]+$"
            return bool(re.match(pattern, browser_str))

        found = set()
        for browser in browsers.browsers():
            exe = (
                browser.get("browser_type")
                or browser.get("display_name")
                or browser.get("name")
            )
            if exe and is_browser_name_safe(exe):
                if exe not in detected_manual:
                    found.add(exe)
        return found
