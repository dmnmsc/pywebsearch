import os
import re
import subprocess
import webbrowser
import gettext
from urllib.parse import quote_plus
from dialogs import Dialogs

_ = gettext.gettext


class KWebSearchApp:
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
        self.cmd_prefix = ">"

    def reload_config(self):
        self.config.load()
        self.aliases = self.config.get_aliases()
        self.default_alias = self.config.get_value("default_alias")
        self.default_browser = self.config.get_value("default_browser")
        self.cmd_prefix = self.config.get_value("cmd_prefix") or ">"

    def launch_url(self, url):
        if self.platform:
            try:
                self.platform.launch_url(url)
                return
            except Exception:
                pass
        webbrowser.open(url, new=2)

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

        cmd_list = cmd.split()
        browser = cmd_list[0] if cmd_list else ""

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

        if history_manager:
            history_manager.add_entry(input_str)

        if input_str.startswith(self.cmd_prefix):
            self.open_direct_url(input_str[len(self.cmd_prefix) :])
        elif ":" in input_str:
            key, query = input_str.split(":", 1)
            key = key.strip()
            query = query.strip()
            if key in self.aliases:
                self.execute_search(key, query)
            else:
                self.duckduckgo_search(input_str)
        else:
            if self.default_alias:
                self.execute_search(self.default_alias, input_str)
            else:
                self.duckduckgo_search(input_str)
