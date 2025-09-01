import os
import subprocess
import sys
import installed_browsers
from platformdirs import user_config_dir, user_data_dir


def is_sandboxed_windows():
    exec_path = sys.executable.lower()
    return "windowsapps" in exec_path and "pythonsoftwarefoundation.python" in exec_path


def get_platform_dirs():
    if is_sandboxed_windows():
        base_path = os.path.expandvars(
            r"%LOCALAPPDATA%\Packages\PythonSoftwareFoundation.Python_8wekyb3d8bbwe\LocalCache\Roaming\dmnmsc\kwebsearch"
        )
        config_dir = base_path
        data_dir = os.path.join(base_path, "data")
    else:
        config_dir = user_config_dir(
            "kwebsearch", appauthor="dmnmsc", ensure_exists=True
        )
        data_dir = user_data_dir("kwebsearch", appauthor="dmnmsc", ensure_exists=True)
    return config_dir, data_dir


def open_config_file(path, verbose=False):
    if verbose:
        print(f"Opening configuration file at: {path}")
    os.startfile(path)


def detect_available_browsers():
    # Using installed_browsers library
    detected = set()
    for browser in installed_browsers.browsers():
        name = browser.get("name")
        if name:
            exe_name = name if name.endswith(".exe") else name + ".exe"
            detected.add(exe_name.lower())
    return detected


ALLOWED_BROWSERS = detect_available_browsers()


def is_browser_available(browser_path):
    exe_name = os.path.basename(browser_path).lower()
    return exe_name in ALLOWED_BROWSERS and bool(
        installed_browsers.do_i_have_installed(exe_name.rstrip(".exe"))
    )


def launch_browser(cmd_list, verbose=False):
    browser = os.path.basename(cmd_list[0]).lower()
    if not is_browser_available(browser):
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


def get_allowed_browsers():
    return sorted(ALLOWED_BROWSERS)


def launch_alias_command(command_line, verbose=False):
    """
    Launch alias commands on Windows using cmd 'start' with proper quoting.
    """
    # Compose complete command line string with quotes around link
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

def get_default_browser_command(default_browser_name):
    default_name = default_browser_name.lower().rstrip(".exe")
    for browser in installed_browsers.browsers():
        name = browser.get("name", "").lower()
        if name == default_name or name.rstrip(".exe") == default_name:
            path = browser.get("location") or browser.get("path")
            if path and os.path.isfile(path):
                return path
    return default_browser_name

import shlex

def launch_url(url, verbose=False):
    # Read the configured default browser string from config
    default_browser_str = read_default_browser_from_config()
    if not default_browser_str:
        if verbose:
            print("[Windows] No default_browser configured, fallback to system default")
        # Launch URL with system default browser using 'start'
        subprocess.Popen(f'start "" "{url}"', shell=True)
        return
    # Parse the default_browser string into executable and arguments
    parts = shlex.split(default_browser_str)
    exec_path_or_name = parts[0]
    args = parts[1:]
    # Resolve the real executable path if available
    exec_path = get_default_browser_command(exec_path_or_name)
    # Build the command list for subprocess (executable + args + url)
    cmd_list = [exec_path] + args + [url]
    if verbose:
        print(f"[Windows] Launching URL with command list: {cmd_list}")
    try:
        # Launch the process without shell=True for safety
        subprocess.Popen(cmd_list)
    except Exception as e:
        if verbose:
            print(f"[Windows] Error launching URL: {e}")
        # Fallback: open with system default browser
        subprocess.Popen(f'start "" "{url}"', shell=True)
