#!/usr/bin/env python3

import os
import sys
import random
import gettext

from PyQt6.QtCore import Qt
from PyQt6.QtGui import QIcon, QAction
from PyQt6.QtWidgets import (
    QApplication,
    QMainWindow,
    QWidget,
    QVBoxLayout,
    QLabel,
    QLineEdit,
)

VERSION = 3.6

# Locale language
script_dir = os.path.dirname(os.path.abspath(__file__))
icon_path = os.path.join(script_dir, "pywebsearch.ico")

locales_dir = os.path.join(script_dir, "locales")
translation = gettext.translation("kwebsearch", locales_dir, fallback=True)
translation.install()
_ = translation.gettext

from search import KWebSearchApp
from app_settings import SettingsManager

VERBOSE = False


class KWebSearchUI(QMainWindow):
    def __init__(self, settings_manager):
        super().__init__()
        self.settings = settings_manager
        self.app = settings_manager.kweb_app
        self.setWindowTitle(_("PyWebSearch"))
        if os.path.exists(icon_path):
            self.setWindowIcon(QIcon(icon_path))
        self.settings.dialogs.parent = self
        self.create_menu_bar()

        main_widget = QWidget()
        self.setCentralWidget(main_widget)
        main_layout = QVBoxLayout()

        random_queries = [
            _("Linux"),
            _("cats"),
            _("kitchen"),
            _("univers"),
            _("Python"),
            _("stock"),
        ]

        example_type = random.choice(["alias", "bang", "url"])
        dynamic_example = ""

        if example_type == "alias":
            if self.settings.aliases:
                random_alias = random.choice(list(self.settings.aliases.keys()))
                random_query = random.choice(random_queries)
                dynamic_example = f"{random_alias}:{random_query}"
        elif example_type == "bang":
            bang_aliases = ["w", "yt", "g", "r"]
            random_bang = random.choice(bang_aliases)
            random_query = random.choice(random_queries)
            dynamic_example = f"!{random_bang} {random_query}"
        elif example_type == "url":
            web_sites = ["github.com", "duckduckgo.com", "en.wikipedia.org"]
            random_site = random.choice(web_sites)
            dynamic_example = f"{self.settings.kweb_app.cmd_prefix}{random_site}"

        info_text = _(
            "Explore the web your way! Use bangs, alias or open URLs.\n\n"
        ) + _(f"🟢 !bang   🔎 alias:query   🌐 >url   ✏️ _help   💡 {dynamic_example}")
        info_label = QLabel(info_text)
        main_layout.addWidget(info_label)
        main_layout.addStretch()

        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText(_("🔎 Explore the web your way!"))
        self.search_input.returnPressed.connect(self.handle_input)
        main_layout.addWidget(self.search_input)

        main_widget.setLayout(main_layout)

    def handle_input(self):
        user_input = self.search_input.text().strip()
        if not user_input:
            return

        commands = {
            "_defaultbrowser": self.settings.set_default_browser,
            "_importbrowsers": self.settings.import_browsers,
            "_alias": self.settings.show_aliases,
            "_newalias": self.settings.create_alias,
            "_edit": self.settings.edit_alias,
            "_default": self.settings.set_default_alias,
            "_resetalias": self.settings.reset_default_alias,
            "_history": self.settings.view_history,
            "_clear": self.settings.clear_history,
            "_prefix": self.settings.set_prefix,
            "_backup": self.settings.backup_config,
            "_restore": self.settings.restore_config,
            "_help": self.settings.show_help,
            "_about": self.settings.about_info,
            "_exit": self.close,
        }

        if user_input in commands:
            commands[user_input]()
        else:
            self.app.process_search(user_input, history_manager=self.settings.history)

        self.search_input.clear()

    def keyPressEvent(self, event):
        if event.key() == Qt.Key.Key_Escape:
            self.close()
        else:
            super().keyPressEvent(event)

    def create_menu_bar(self):
        menu_bar = self.menuBar()
        menus = {
            "Search": [
                (_("Select alias..."), self.settings.show_aliases),
                (_("View history"), self.settings.view_history),
                ("---", None),
                (_("Clear history"), self.settings.clear_history),
                (_("Open URL..."), self.settings.open_url_dialog),
            ],
            "Alias": [
                (_("Create new alias..."), self.settings.create_alias),
                (_("Edit alias file"), self.settings.edit_alias),
                ("---", None),
                (_("Set default alias..."), self.settings.set_default_alias),
                (_("Reset default alias"), self.settings.reset_default_alias),
            ],
            "Settings": [
                (_("Set default browser..."), self.settings.set_default_browser),
                (_("Change URL prefix..."), self.settings.set_prefix),
                ("---", None),
                (_("Create backup..."), self.settings.backup_config),
                (_("Restore backup..."), self.settings.restore_config),
                ("---", None),
                (_("Import extra browsers..."), self.settings.import_browsers),
            ],
            "Help": [
                (_("Help"), self.settings.show_help),
                (_("About..."), self.settings.about_info),
            ],
        }

        for menu_name, actions in menus.items():
            menu = menu_bar.addMenu(_(menu_name))
            for action_name, handler in actions:
                if action_name == "---":
                    menu.addSeparator()
                else:
                    action = QAction(action_name, self)
                    action.triggered.connect(handler)
                    menu.addAction(action)


def main():
    global VERBOSE
    if len(sys.argv) > 1 and sys.argv[1] in ("--help", "-h"):
        print(
            _(
                """pywebsearch - Custom web search tool
Usage:
pywebsearch [options] [query]

Options:
--help, -h            Show this help and exit.
--verbose             Verbose mode (show executed commands).

Examples:
pywebsearch --help
pywebsearch '!g mechanical keyboard'
pywebsearch '>github.com'
pywebsearch 'g:cockatoo'
"""
            )
        )
        sys.exit(0)

    if len(sys.argv) > 1 and sys.argv[1] == "--verbose":
        VERBOSE = True
        sys.argv.pop(1)

    current_platform = sys.platform
    if current_platform.startswith("linux"):
        from linux import LinuxHelper as platform_mod
    elif current_platform == "win32":
        from windows import WindowsHelper as platform_mod
    else:
        from linux import LinuxHelper as platform_mod

    # Accurate config path for integration with SettingsManager setup:
    # Use the same logic as SettingsManager for config_dir:
    script_dir = os.path.dirname(os.path.abspath(__file__))
    # If you want absolute per-user config location, use platformdirs logic:
    from platformdirs import user_config_dir
    config_dir = user_config_dir("kwebsearch", appauthor="dmnmsc", ensure_exists=True)
    conf_path = os.path.join(config_dir, "kwebsearch.conf")
    from config import ConfigHandler
    config_handler_instance = ConfigHandler(conf_path)

    # Instantiate and attach config to platform helper:
    platform_helper = platform_mod()
    platform_helper.config = config_handler_instance

    app = QApplication(sys.argv)
    kweb_app = KWebSearchApp(platform_module=platform_helper)
    settings = SettingsManager(kweb_app, version=VERSION)
    main_window = KWebSearchUI(settings)
    main_window.show()
    if len(sys.argv) > 1:
        kweb_app.process_search(
            " ".join(sys.argv[1:]), history_manager=settings.history
        )
        sys.exit(0)
    sys.exit(app.exec())

    main_window = KWebSearchUI(settings)
    main_window.show()

    if len(sys.argv) > 1:
        kweb_app.process_search(
            " ".join(sys.argv[1:]), history_manager=settings.history
        )
        sys.exit(0)

    sys.exit(app.exec())


if __name__ == "__main__":
    main()
