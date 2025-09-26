#!/usr/bin/env python3

import os
import sys
import random
import gettext

from platformdirs import user_config_dir

from pywebsearch.search import PyWebSearchApp
from pywebsearch.app_settings import SettingsManager


from PyQt6.QtCore import Qt
from PyQt6.QtGui import QAction, QShortcut, QKeySequence, QIcon
from PyQt6.QtWidgets import (
    QApplication,
    QMainWindow,
    QWidget,
    QVBoxLayout,
    QLabel,
    QLineEdit,
    QSystemTrayIcon,
    QMenu,
)

VERSION = 3.6

# Icon
if sys.platform.startswith("linux"):
    from pywebsearch.linux import get_icon
else:
    from pywebsearch.windows import get_icon


def load_icon():
    return get_icon()


# Locale language
script_dir = os.path.dirname(os.path.abspath(__file__))

locales_dir = os.path.join(script_dir, "locales")
translation = gettext.translation("pywebsearch", locales_dir, fallback=True)
translation.install()
_ = translation.gettext

VERBOSE = False


class PyWebSearchUI(QMainWindow):
    def __init__(self, settings_manager):
        super().__init__()
        self.settings = settings_manager
        self.app = settings_manager.pyweb_app
        self.setWindowTitle(_("PyWebSearch"))
        self.setWindowIcon(load_icon())
        self.settings.dialogs.parent = self
        self.script_dir = os.path.dirname(os.path.abspath(__file__))
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
            dynamic_example = f"{self.settings.pyweb_app.cmd_prefix}{random_site}"

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

        shortcut = QShortcut(QKeySequence("F5"), self)
        shortcut.activated.connect(self.reload_configuration)

        # Added for tray icon functionality in Windows
        self.tray_icon = None
        self.is_quitting = False

    def closeEvent(self, event):
        if sys.platform.startswith("win32"):
            if not self.is_quitting:
                event.ignore()
                self.hide()
                if self.tray_icon:
                    self.tray_icon.showMessage(
                        "PyWebSearch",
                        "La aplicación sigue funcionando en la bandeja de sistema.",
                        QSystemTrayIcon.MessageIcon.Information,
                        3000
                    )
        else:
            event.accept()

    def reload_configuration(self):
        self.settings.reload_config()
        self.settings.dialogs.show_message_box("⚡ Configuration reloaded (F5)")

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
                ("icons/alias.svg", _("Select alias"), self.settings.show_aliases),
                ("icons/history.svg", _("View history"), self.settings.view_history),
                (None, "---", None),
                ("icons/clear.svg", _("Clear history"), self.settings.clear_history),
                ("icons/url.svg", _("Open URL"), self.settings.open_url_dialog),
            ],
            "Alias": [
                ("icons/new_alias.svg", _("Create new alias"), self.settings.create_alias),
                ("icons/edit.svg", _("Edit alias file"), self.settings.edit_alias),
                (None, "---", None),
                ("icons/default_alias.svg", _("Set default alias"), self.settings.set_default_alias),
                ("icons/reset_alias.svg", _("Reset default alias"), self.settings.reset_default_alias),
            ],
            "Settings": [
                ("icons/browser.svg", _("Set default browser"), self.settings.set_default_browser),
                ("icons/url_prefix.svg", _("Change URL prefix"), self.settings.set_prefix),
                (None, "---", None),
                ("icons/backup.svg", _("Create backup"), self.settings.backup_config),
                ("icons/restore.svg", _("Restore backup"), self.settings.restore_config),
                (None, "---", None),
                ("icons/rocket.svg", _("Import extra browsers"), self.settings.import_browsers),
                ("icons/reload.svg", _("Reload conf file"), self.reload_configuration),
            ],
            "Help": [
                ("icons/help.svg", _("Help"), self.settings.show_help),
                ("icons/about.svg", _("About..."), self.settings.about_info),
            ],
        }

        for menu_name, actions in menus.items():
            menu = menu_bar.addMenu(_(menu_name))
            for icon_path, action_name, handler in actions:
                if action_name == "---":
                    menu.addSeparator()
                else:
                    if icon_path:
                        full_icon_path = os.path.join(self.script_dir, icon_path)
                        icon = QIcon(full_icon_path)
                    else:
                        icon = QIcon()
                    action = QAction(icon, action_name, self)
                    if handler:
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
        from pywebsearch.linux import LinuxHelper as platform_mod
    elif current_platform == "win32":
        from pywebsearch.windows import WindowsHelper as platform_mod
    else:
        from pywebsearch.linux import LinuxHelper as platform_mod

    # User config path determined via platformdirs for cross-platform compatibility
    config_dir = user_config_dir("pywebsearch", appauthor="dmnmsc", ensure_exists=True)
    conf_path = os.path.join(config_dir, "pywebsearch.conf")
    from pywebsearch.config import ConfigHandler
    config_handler_instance = ConfigHandler(conf_path)

    # Instantiate and attach config to platform helper:
    platform_helper = platform_mod()
    platform_helper.config = config_handler_instance

    # --- Single Instance Check ---
    if platform_helper.check_single_instance():
        platform_helper.send_activation_message()
        sys.exit(0)

    app = QApplication(sys.argv)
    app.setApplicationName("pywebsearch")
    app.setApplicationDisplayName("PyWebSearch")
    app.setDesktopFileName("pywebsearch")

    pyweb_app = PyWebSearchApp(platform_module=platform_helper)
    pyweb_app.platform_helper = platform_helper
    settings = SettingsManager(pyweb_app, version=VERSION)

    main_window = PyWebSearchUI(settings)
    platform_helper.main_window = main_window

    tray_icon = None
    if hasattr(settings.pyweb_app, "platform_helper"):
        tray_icon = settings.pyweb_app.platform_helper.init_tray_icon(main_window)
        if tray_icon:
            main_window.tray_icon = tray_icon

    main_window.show()

    if len(sys.argv) > 1:
        pyweb_app.process_search(
            " ".join(sys.argv[1:]), history_manager=settings.history
        )
        sys.exit(0)
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
