#!/usr/bin/env python3
import sys
from PyQt6.QtWidgets import (
    QApplication,
    QMainWindow,
    QWidget,
    QVBoxLayout,
    QLabel,
    QLineEdit,
)
from PyQt6.QtGui import QIcon, QAction
from PyQt6.QtCore import Qt
from common import KWebSearchApp, icon_path, _

VERBOSE = False


class KWebSearchUI(QMainWindow):
    def __init__(self, app):
        super().__init__()
        self.app = app
        self.setWindowTitle(_("KWebSearch"))
        self.setWindowIcon(QIcon(icon_path))
        self.default_browser = ""
        self.app.dialogs.parent = self
        self.create_menu_bar()
        main_widget = QWidget()
        self.setCentralWidget(main_widget)
        main_layout = QVBoxLayout()
        import random

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
            random_alias = random.choice(list(self.app.aliases.keys()))
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
            dynamic_example = f"{self.app.cmd_prefix}{random_site}"
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
            "_defaultbrowser": self.app.set_default_browser,
            "_alias": self.app.show_aliases,
            "_newalias": self.app.create_alias,
            "_edit": self.app.edit_alias,
            "_default": self.app.set_default_alias,
            "_resetalias": self.app.reset_default_alias,
            "_history": self.app.view_history,
            "_clear": self.app.clear_history,
            "_prefix": self.app.set_prefix,
            "_backup": self.app.backup_config,
            "_restore": self.app.restore_config,
            "_help": self.app.show_help,
            "_about": self.app.about_info,
            "_exit": self.close,
        }
        if user_input in commands:
            commands[user_input]()
        else:
            self.app.process_search(user_input)
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
                (_("Select alias..."), self.app.show_aliases),
                (_("View history"), self.app.view_history),
                ("---", None),
                (_("Clear history"), self.app.clear_history),
                (_("Open URL..."), self.app.open_url_dialog),
            ],
            "Alias": [
                (_("Create new alias..."), self.app.create_alias),
                (_("Edit alias file"), self.app.edit_alias),
                ("---", None),
                (_("Set default alias..."), self.app.set_default_alias),
                (_("Reset default alias"), self.app.reset_default_alias),
            ],
            "Settings": [
                (_("Set default browser..."), self.app.set_default_browser),
                (_("Change URL prefix..."), self.app.set_prefix),
                ("---", None),
                (_("Create backup..."), self.app.backup_config),
                (_("Restore backup..."), self.app.restore_config),
            ],
            "Help": [
                (_("Help"), self.app.show_help),
                (_("About..."), self.app.about_info),
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
                """kwebsearch - Custom web search tool
Usage:
    kwebsearch [options] [query]
Options:
    --help, -h       Show this help and exit.
    --verbose        Verbose mode (show executed commands).
Examples:
    kwebsearch --help
    kwebsearch '!g mechanical keyboard'
    kwebsearch '>github.com'
    kwebsearch 'g:cockatoo'
"""
            )
        )
        sys.exit(0)

    if len(sys.argv) > 1 and sys.argv[1] == "--verbose":
        VERBOSE = True
        sys.argv.pop(1)

    # Choose platform module by running platform detection
    current_platform = sys.platform
    if current_platform.startswith("linux"):
        import linux as platform_mod
    elif current_platform == "win32":
        import windows as platform_mod
    else:
        platform_mod = linux  # fallback generic # noqa: F821

    qt_app = QApplication(sys.argv)
    app_logic = KWebSearchApp(platform_module=platform_mod)

    if len(sys.argv) > 1:
        app_logic.process_search(" ".join(sys.argv[1:]))
        sys.exit(0)

    main_window = KWebSearchUI(app_logic)
    main_window.show()
    sys.exit(qt_app.exec())


if __name__ == "__main__":
    main()
