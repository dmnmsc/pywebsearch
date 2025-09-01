#!/usr/bin/env python3
import os
import glob
import shutil
import subprocess
from platformdirs import user_config_dir, user_data_dir


def get_platform_dirs():
    config_dir = user_config_dir("kwebsearch", appauthor="dmnmsc", ensure_exists=True)
    data_dir = user_data_dir("kwebsearch", appauthor="dmnmsc", ensure_exists=True)
    return config_dir, data_dir


def open_config_file(path, verbose=False):
    if verbose:
        subprocess.run(["xdg-open", path])
    else:
        subprocess.Popen(
            ["xdg-open", path],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )


def detect_available_browsers():
    # Patterns for popular browser families
    browser_patterns = [
        "firefox*",  # firefox, firefoxpwa, firefoxtest
        "chromium*",  # chromium, chromium-browser, etc.
        "google-chrome*",  # google-chrome-stable, google-chrome-beta, etc.
        "brave*",  # brave, brave-browser
        "opera*",  # opera, opera-beta
        "vivaldi*",  # vivaldi
        "microsoft-edge*",  # microsoft-edge
    ]
    detected = set()
    for pattern in browser_patterns:
        for path_entry in os.environ.get("PATH", "").split(os.pathsep):
            for match in glob.glob(os.path.join(path_entry, pattern)):
                exe = os.path.basename(match)
                if os.access(match, os.X_OK):
                    detected.add(exe)
    # Add text-based browsers if present
    for text_browser in ["lynx", "w3m", "links"]:
        if shutil.which(text_browser):
            detected.add(text_browser)
    return detected


ALLOWED_BROWSERS = detect_available_browsers()


def is_browser_available(browser_name):
    return browser_name in ALLOWED_BROWSERS and shutil.which(browser_name) is not None


def launch_browser(cmd_list, verbose=False):
    browser = os.path.basename(cmd_list[0])
    if not is_browser_available(browser):
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


def get_allowed_browsers():
    return sorted(ALLOWED_BROWSERS)
