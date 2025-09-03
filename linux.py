#!/usr/bin/env python3
import glob
import os
import shutil
import subprocess

from platform_base import PlatformHelper


class LinuxHelper(PlatformHelper):

    def get_platform_dirs(self):
        from platformdirs import user_config_dir, user_data_dir

        config_dir = user_config_dir(
            "kwebsearch",
            appauthor="dmnmsc",
            ensure_exists=True,
        )

        data_dir = user_data_dir("kwebsearch", appauthor="dmnmsc", ensure_exists=True)
        return config_dir, data_dir

    def open_config_file(self, path, verbose=False):
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

        for text_browser in ["lynx", "w3m", "links"]:
            if shutil.which(text_browser):
                detected.add(text_browser)
        return detected

    def is_browser_available(self, browser_name):
        return (
            browser_name in self.detect_available_browsers()
            and shutil.which(browser_name) is not None
        )

    def launch_browser(self, cmd_list, verbose=False):
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

    def launch_default_system_url(self, url, verbose=False):
        if verbose:
            print(f"[Linux] Launching default system URL fallback with xdg-open: {url}")
        subprocess.Popen(
            ["xdg-open", url],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            start_new_session=True,
        )
