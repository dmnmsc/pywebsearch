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
