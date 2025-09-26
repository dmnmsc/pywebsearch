import os
import shlex


class PlatformHelper:
    def get_platform_dirs(self):
        raise NotImplementedError

    def open_config_file(self, path, verbose=False):
        raise NotImplementedError

    def detect_available_browsers(self):
        raise NotImplementedError

    def is_browser_available(self, browser_name):
        raise NotImplementedError

    def read_default_browser_from_config(self):
        config_dir, _ = self.get_platform_dirs()
        conf_path = os.path.join(config_dir, "pywebsearch.conf")

        if not os.path.exists(conf_path):
            return ""

        with open(conf_path, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if line.startswith("default_browser="):
                    return line.split("=", 1)[1].strip().strip('"')
        return ""

    def launch_browser(self, cmd_list, verbose=False):
        raise NotImplementedError

    def launch_url(self, url, verbose=False):
        default_browser_str = self.read_default_browser_from_config()
        if default_browser_str:
            parts = shlex.split(default_browser_str)
            exec_path_or_name = parts[0]
            args = parts[1:]
            cmd_list = [exec_path_or_name] + args + [url]
            if not self.launch_browser(cmd_list, verbose):
                if verbose:
                    print(
                        f"[{self.__class__.__name__}] Could not launch configured browser, falling back."
                    )
                self.launch_default_system_url(url, verbose)
        else:
            if verbose:
                print(
                    f"[{self.__class__.__name__}] No default_browser configured, using system fallback."
                )
            self.launch_default_system_url(url, verbose)

    def launch_default_system_url(self, url, verbose=False):
        raise NotImplementedError

    def init_tray_icon(self, main_window):
        """
        Initialize the system tray icon for the platform.
        Base implementation does nothing.
        """
        return None

    def check_single_instance(self):
        """
        Check if an instance is already running.
        Base implementation returns False (no single instance).
        """
        return False

    def send_activation_message(self):
        """
        Send a message to the existing instance to activate window.
        Base implementation no-op.
        """
        pass
