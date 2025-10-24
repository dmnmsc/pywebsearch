import os
import re
import subprocess
import webbrowser
import gettext
import shlex
from urllib.parse import quote_plus
from pywebsearch.dialogs import Dialogs


_ = gettext.gettext


class PyWebSearchApp:
    """
    Core search logic, URL handling, alias execution, and query processing.
    """

    supported_browsers = {
        "firefox",
        "chromium",
        "brave",
        "google-chrome",
        "chrome",
        "opera",
        "safari",
    }

    def __init__(self, platform_module=None):
        self.platform = platform_module
        self.dialogs = Dialogs()
        self.aliases = {}
        self.default_alias = ""
        self.default_browser = ""
        self.alt_browser = ""
        self.cmd_prefix = ">"
        self.alt_cmd_prefix = "@"

    def reload_config(self):
        self.config.load()
        self.aliases = self.config.get_aliases()
        self.default_alias = self.config.get_value("default_alias")
        self.default_browser = self.config.get_value("default_browser")
        self.cmd_prefix = self.config.get_value("cmd_prefix") or ">"
        self.alt_cmd_prefix = self.config.get_value("alt_cmd_prefix") or "@"
        self.alt_browser = self.config.get_value("alt_browser")

    def launch_url(self, url, browser=None):
        if self.platform:
            try:
                if browser:
                    return self.platform.launch_url(url, browser=browser)
                else:
                    return self.platform.launch_url(url)
            except Exception:
                pass
        if browser:
            try:
                wb = webbrowser.get(browser)
                return wb.open(url, new=2)
            except Exception:
                return webbrowser.open(url, new=2)
        return webbrowser.open(url, new=2)

    def open_direct_url(self, url):
        if not re.match(r"^[a-zA-Z]+://", url):
            url = f"https://{url}"
        self.launch_url(url)

    def duckduckgo_search(self, query):
        url = f"https://duckduckgo.com/?q={quote_plus(query)}"
        self.launch_url(url)

    def execute_search(self, key, query):
        alias_data = self.aliases.get(key)
        if not alias_data:
            self.duckduckgo_search(query)
            return

        cmd_template = alias_data["cmd"].strip('"')
        query_encoded = quote_plus(query)
        cmd = re.sub(r"\$query", query_encoded, cmd_template)

        if cmd.startswith(("http://", "https://")):
            self.launch_url(cmd)
            return

        # Parse command safely into list for platform processing
        cmd_list = shlex.split(cmd)
        browser = cmd_list[0].lower() if cmd_list else ""

        # For Windows and Linux, delegate alias execution to platform helper if possible
        if hasattr(self, "platform") and hasattr(self.platform, "launch_alias_command"):
            try:
                if self.platform.launch_alias_command(cmd, verbose=True):
                    return
            except Exception:
                pass

        if browser in self.supported_browsers:
            try:
                subprocess.Popen(
                    cmd,
                    shell=True,
                    stdout=subprocess.DEVNULL,
                    stderr=subprocess.DEVNULL,
                    start_new_session=True,
                )
                return
            except Exception:
                self.duckduckgo_search(query)
                return

        try:
            subprocess.Popen(
                cmd,
                shell=True,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
                start_new_session=True,
            )
        except Exception:
            self.duckduckgo_search(query)

    def process_search(self, input_str, history_manager=None):
        input_str = input_str.strip()
        if not input_str:
            return

        if self.alt_cmd_prefix and input_str.startswith(self.alt_cmd_prefix):
            actual_query = input_str[len(self.alt_cmd_prefix):].strip()
            if self.cmd_prefix and actual_query.startswith(self.cmd_prefix):
                url = actual_query[len(self.cmd_prefix):].strip()
                self.launch_url(url, browser=self.alt_browser)
                return
            if history_manager:
                history_manager.add_entry(input_str)
            if ":" in actual_query:
                key, query = actual_query.split(":", 1)
                key = key.strip()
                query = query.strip()
                alias_data = self.aliases.get(key)
                if not alias_data:
                    url = f"https://duckduckgo.com/?q={quote_plus(actual_query)}"
                    self.launch_url(url, browser=self.alt_browser)
                    return
                cmd_template = alias_data["cmd"].strip('"')
                query_encoded = quote_plus(query)
                cmd = re.sub(r"\$query", query_encoded, cmd_template)
                if cmd.startswith(("http://", "https://")):
                    self.launch_url(cmd, browser=self.alt_browser)
                    return
                if hasattr(self, "platform") and hasattr(self.platform, "launch_alias_command"):
                    try:
                        if self.platform.launch_alias_command(cmd, browser=self.alt_browser, verbose=True):
                            return
                    except Exception:
                        pass
                try:
                    subprocess.Popen(
                        cmd,
                        shell=True,
                        stdout=subprocess.DEVNULL,
                        stderr=subprocess.DEVNULL,
                        start_new_session=True,
                    )
                    return
                except Exception:
                    self.duckduckgo_search(query)
                    return
            else:
                url = f"https://duckduckgo.com/?q={quote_plus(actual_query)}"
                self.launch_url(url, browser=self.alt_browser)
            return

        # Si no es alt_cmd_prefix, continuación normal:
        if history_manager:
            history_manager.add_entry(input_str)

        if self.cmd_prefix and input_str.startswith(self.cmd_prefix):
            self.open_direct_url(input_str[len(self.cmd_prefix):])
            return

        if ":" in input_str:
            key, query = input_str.split(":", 1)
            key = key.strip()
            query = query.strip()
            if key in self.aliases:
                self.execute_search(key, query)
                return
            else:
                self.duckduckgo_search(input_str)
                return

        if self.default_alias:
            self.execute_search(self.default_alias, input_str)
        else:
            self.duckduckgo_search(input_str)
