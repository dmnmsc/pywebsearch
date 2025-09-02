#!/usr/bin/env python3
import os
import glob
import shutil
import subprocess
import shlex
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
    # Add text-based browsers if present
    for text_browser in ["lynx", "w3m", "links"]:
        if shutil.which(text_browser):
            detected.add(text_browser)
    return detected


ALLOWED_BROWSERS = detect_available_browsers()


def is_browser_available(browser_name):
    return browser_name in ALLOWED_BROWSERS and shutil.which(browser_name) is not None


def read_default_browser_from_config():
    config_dir, _ = get_platform_dirs()
    conf_path = os.path.join(config_dir, "kwebsearch.conf")
    if not os.path.exists(conf_path):
        return ""
    with open(conf_path, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line.startswith("default_browser="):
                return line.split("=", 1)[1].strip().strip('"')
    return ""


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


def launch_url(url, verbose=False):
    # Read default_browser from config
    default_browser_str = read_default_browser_from_config()
    if default_browser_str:
        # Parse the browser command with arguments
        parts = shlex.split(default_browser_str)
        exec_path_or_name = parts[0]
        args = parts[1:]
        # Build the full command list with URL at the end
        cmd_list = [exec_path_or_name] + args + [url]
        # Try to launch with the configured browser
        if not launch_browser(cmd_list, verbose):
            if verbose:
                print(
                    f"[Linux] Failed to launch custom browser, falling back to xdg-open"
                )
            # fallback to xdg-open
            subprocess.Popen(
                ["xdg-open", url],
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
            )
        return
    # If not configured, fallback to xdg-open
    if verbose:
        print(f"[Linux] No default_browser configured, using xdg-open")
    subprocess.Popen(
        ["xdg-open", url],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )


def get_allowed_browsers():
    return sorted(ALLOWED_BROWSERS)
