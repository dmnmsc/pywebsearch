import os
import gettext
import re
import webbrowser
import sys
from datetime import datetime
from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import QMessageBox
from dialogs import Dialogs
from config import ConfigHandler
from history import HistoryManager
from backup import backup_files, restore_files
from alias import AliasManager

_ = gettext.gettext


class SettingsManager:
    def __init__(self, kweb_app, version="dev"):
        self.kweb_app = kweb_app
        self.dialogs = kweb_app.dialogs
        self.version = version

        if self.kweb_app.platform:
            self.config_dir, self.data_dir = self.kweb_app.platform.get_platform_dirs()
        else:
            from platformdirs import user_config_dir, user_data_dir

            self.config_dir = user_config_dir(
                "kwebsearch", appauthor="dmnmsc", ensure_exists=True
            )
            self.data_dir = user_data_dir(
                "kwebsearch", appauthor="dmnmsc", ensure_exists=True
            )

        self.conf_path = os.path.join(self.config_dir, "kwebsearch.conf")
        self.hist_path = os.path.join(self.data_dir, "kwebsearch_history")
        self.backup_dir = os.path.join(self.data_dir, "backup")

        self.config = ConfigHandler(self.conf_path)
        self.history = HistoryManager(self.hist_path)

        self.kweb_app.config = self.config
        self.kweb_app.history = self.history
        self.kweb_app.conf_path = self.conf_path
        self.kweb_app.hist_path = self.hist_path
        self.kweb_app.backup_dir = self.backup_dir

        self.aliases = self.config.get_aliases()
        self.kweb_app.aliases = self.aliases
        self.kweb_app.default_alias = self.config.get_value("default_alias")
        self.kweb_app.default_browser = self.config.get_value("default_browser")
        self.kweb_app.cmd_prefix = self.config.get_value("cmd_prefix") or ">"

        self.setup_directories()

        self.alias_manager = AliasManager(
            self.dialogs,
            self.conf_path,
            self.aliases,
            self.reload_config,
            self.kweb_app.platform,
            self.config,
            self.kweb_app.default_alias,
            self.kweb_app.process_search,
            self.kweb_app.duckduckgo_search,
            self.history,
        )

    def setup_directories(self):
        os.makedirs(self.config_dir, exist_ok=True)
        os.makedirs(self.data_dir, exist_ok=True)
        os.makedirs(self.backup_dir, exist_ok=True)

        if not os.path.exists(self.hist_path):
            with open(self.hist_path, "a", encoding="utf-8"):
                pass
        if not os.path.exists(self.conf_path):
            self.config.create_default_config()

    def reload_config(self):
        self.config.load()
        self.aliases = self.config.get_aliases()
        self.kweb_app.aliases = self.aliases
        self.kweb_app.default_alias = self.config.get_value("default_alias")
        self.kweb_app.default_browser = self.config.get_value("default_browser")
        self.kweb_app.cmd_prefix = self.config.get_value("cmd_prefix") or ">"

    def show_aliases(self):
        self.alias_manager.show_aliases()

    def create_alias(self):
        self.alias_manager.create_alias()

    def edit_alias(self):
        self.alias_manager.edit_alias()

    def set_default_alias(self):
        self.alias_manager.set_default_alias()

    def reset_default_alias(self):
        self.alias_manager.reset_default_alias()

    def set_prefix(self):
        new_prefix = self.dialogs.get_input(
            _("Change URL prefix"),
            _(
                f"Current symbol: {self.kweb_app.cmd_prefix}\n\nEnter new prefix to open URLs directly:"
            ),
            text=self.kweb_app.cmd_prefix,
            select_text=True,
        )
        if new_prefix is None or not new_prefix or " " in new_prefix:
            self.dialogs.show_message_box(
                _("Invalid prefix. No changes made."),
                _("Error"),
                icon=QMessageBox.Icon.Warning,
            )
            return
        self.config.set_value("cmd_prefix", new_prefix)
        self.dialogs.show_message_box(_("✅ Prefix updated to: ") + new_prefix)
        self.reload_config()

    def set_default_browser(self):
        self.reload_config()
        current = self.kweb_app.default_browser or ""
        new_browser = self.dialogs.get_input(
            _("Set default browser command"),
            _(
                "Enter the default browser command with options (e.g. firefox --new-tab):"
            ),
            text=current,
            select_text=True,
        )
        if new_browser is None:
            return
        self.config.set_value("default_browser", new_browser)
        self.dialogs.show_message_box(
            _("✅ Default browser updated to: ") + new_browser
        )
        self.reload_config()

    def backup_config(self):
        options_map = [
            (_("⚙️ Aliases (kwebsearch.conf)"), True),
            (_("🕘 History (kwebsearch_history)"), True),
            (_("📦 Both"), True),
        ]
        selection = self.dialogs.show_radio_list_dialog(
            _("Export configuration"), _("What do you want to export?"), options_map
        )
        if not selection:
            return
        selected_option = options_map[selection - 1][0]
        files_map = {
            _("⚙️ Aliases (kwebsearch.conf)"): [self.kweb_app.conf_path],
            _("🕘 History (kwebsearch_history)"): [self.kweb_app.hist_path],
            _("📦 Both"): [self.kweb_app.conf_path, self.kweb_app.hist_path],
        }
        dest = backup_files(files_map[selected_option], self.kweb_app.backup_dir)
        self.dialogs.show_message_box(_("✅ Aliases and history exported in:\n") + dest)

    def restore_config(self):
        backups = sorted(
            (
                d
                for d in os.listdir(self.kweb_app.backup_dir)
                if d.startswith("20")
                and os.path.isdir(os.path.join(self.kweb_app.backup_dir, d))
            ),
            reverse=True,
        )
        if not backups:
            self.dialogs.show_message_box(
                _("❌ No backups found."), _("Error"), QMesaBox.Icon.Critical
            )
            return
        selected_backup_name = self.dialogs.show_list_dialog(
            _("Restore configuration"), _("Select backup to restore:"), backups
        )
        if not selected_backup_name:
            return
        full_path = os.path.join(self.kweb_app.backup_dir, selected_backup_name)
        has_conf = os.path.exists(os.path.join(full_path, "kwebsearch.conf"))
        has_hist = os.path.exists(os.path.join(full_path, "kwebsearch_history"))
        if not has_conf and not has_hist:
            self.dialogs.show_message_box(
                _("❌ Selected backup does not contain valid files."),
                _("Error"),
                QMesaBox.Icon.Critical,
            )
            return
        restore_options = [
            (_("⚙️ Aliases (kwebsearch.conf)"), has_conf),
            (_("🕘 History (kwebsearch_history)"), has_hist),
        ]
        if has_conf and has_hist:
            restore_options.append((_("📦 Both"), True))
        selection = self.dialogs.show_radio_list_dialog(
            _("Content detected"),
            _("Choose what to restore from backup:"),
            restore_options,
        )
        if not selection:
            return
        if selection == 1 and has_conf:
            restore_files(full_path, [self.kweb_app.conf_path])
            self.dialogs.show_message_box(_("✅ Aliases restored successfully"))
        elif selection == 2 and has_hist:
            restore_files(full_path, [self.kweb_app.hist_path])
            self.dialogs.show_message_box(_("✅ History restored successfully"))
        elif selection == 3 and has_conf and has_hist:
            restore_files(full_path, [self.kweb_app.conf_path, self.kweb_app.hist_path])
            self.dialogs.show_message_box(
                _("✅ Aliases and history restored successfully")
            )

    def view_history(self):
        if not os.path.exists(self.hist_path) or os.path.getsize(self.hist_path) == 0:
            self.dialogs.show_message_box(_("ℹ️ No search history available yet."))
            return
        with open(self.hist_path, "r", encoding="utf-8") as f:
            history = [line.strip() for line in f if line.strip()]
        if not history:
            self.dialogs.show_message_box(_("ℹ️ No search history available yet."))
            return
        history.reverse()
        selected = self.dialogs.show_searchable_list_dialog(
            _("Search history"), _("Select a previous search:"), history
        )
        if selected:
            self.kweb_app.process_search(selected, history_manager=self.history)

    def clear_history(self):
        if self.dialogs.show_yes_no_box(
            _("Are you sure you want to clear the search history?")
        ):
            open(self.hist_path, "w", encoding="utf-8").close()
            self.dialogs.show_message_box(_("✅ Search history cleared successfully."))

    def open_url_dialog(self):
        url = self.dialogs.get_input(
            _("Enter the URL to open:"),
            _("Enter the URL to open (e.g., example.com or https://example.com):"),
        )
        if url:
            self.kweb_app.open_direct_url(url)

    def import_browsers(self):
        use_deep_scan = False
        # On Windows, offer deep scan to the user
        if sys.platform.startswith("win"):
            use_deep_scan = self.dialogs.show_yes_no_box(
                "Deeper scan?",
                "A quick scan for extra browsers will be performed. Do you want to scan exhaustively? (This is slow, only needed if your browser isn't found.)"
            )
        # Use platform helper for actual search
            new_browsers = self.kweb_app.platform.import_extra_browsers(use_deep_scan)
        else:
            new_browsers = self.kweb_app.platform.import_extra_browsers()
        if not new_browsers:
            self.dialogs.show_message_box("No new browsers found.")
            return
        # Allow user to pick which browsers to add (shows all at once here)
        chosen = self.dialogs.show_list_dialog(
            "Add browsers",
            "Select browsers to add to your configuration:",
            list(new_browsers)
        )
        if chosen:
            # Store in config (as comma-separated)
            existing = self.config.get_value("extra_browsers").split(",")
            updated = set(existing) | {chosen}
            # Re-validate for safety!
            safe_updated = [b for b in updated if self.kweb_app.platform.is_browser_name_safe(b)]
            self.config.set_value("extra_browsers", ",".join(safe_updated))
            self.dialogs.show_message_box("✅ Browsers added successfully.")

    def show_help(self):
        help_text = _(
            """
🧾 <b>HELP - Using kwebsearch</b>
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
<pre>
🔎 <b>SEARCH METHODS:</b>

🟢 <b><i>!bang:</i> Perform quick searches with DuckDuckGo aliases.</b>
    → <i>Example: !w solar energy</i>  (Wikipedia search)
    → <i>Example: !gh kwebsearch</i> (GitHub search)

🔎 <b><i>alias:query:</i> Use custom aliases defined by you.</b>
    → <i>Example: g:mechanical keyboard</i> (Google search)
    → <i>Example: w:Linux</i> (Wikipedia Search)

🌐 <b><i>url:</i> Open a URL directly in the browser.</b>
    → <i>Example: >github.com</i>
    → <i>Example: >es.wikipedia.org/wiki/Bash</i>

<b>✏️ Internal commands (type in the prompt):</b><br>
<table border="1" cellspacing="0" cellpadding="4">
<tr><th>Command</th><th>Description</th></tr>
<tr><td><b>_alias</b></td><td>Select alias for searching</td></tr>
<tr><td><b>_newalias</b></td><td>Create new alias</td></tr>
<tr><td><b>_edit</b></td><td>Edit alias file manually</td></tr>
<tr><td><b>_default</b></td><td>Set default alias</td></tr>
<tr><td><b>_resetalias</b></td><td>Reset default alias to DuckDuckGo</td></tr>
<tr><td><b>_defaultbrowser</b></td><td>Set default browser</td></tr>
<tr><td><b>_history</b></td><td>View recent search history</td></tr>
<tr><td><b>_clear</b></td><td>Clear history</td></tr>
<tr><td><b>_prefix</b></td><td>Change symbol for opening URLs directly (e.g., &gt;)</td></tr>
<tr><td><b>_backup</b></td><td>Create backup of config and history</td></tr>
<tr><td><b>_restore</b></td><td>Restore existing backup</td></tr>
<tr><td><b>_help</b></td><td>Show this help</td></tr>
<tr><td><b>_about</b></td><td>About kwebsearch</td></tr>
<tr><td><b>_exit</b></td><td>Exit the program</td></tr>
</table>
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
"""
        )
        self.dialogs.show_message_box(help_text)

    def about_info(self):
        about_text = _(
            f"""<b>🛠️ kwebsearch - Custom web search tool</b><br>
    Version: <b>{self.version}</b><br>
    Author: <i>dmnmsc</i><br>
    Last updated: <u>{datetime.now().strftime("%Y-%m-%d")}</u><br>
    <br>
    📌 <b>What is kwebsearch?</b><br>
    A simple and practical tool to perform fast searches and open web pages using customizable aliases and !bangs, with a user-friendly GUI.<br>
    <br>
    ⭐ <b>Main features:</b><br>
    • Quick alias searches<br>
    • <i>DuckDuckGo !bangs</i> integration for versatile searches<br>
    • Direct URL opening</b> with configurable prefix<br>
    • Local search history auto saved<br>
    • Configuration and history backup and restore<br>
    <br>
    📂 <b>Main files:</b><br>
    • <b>Alias configuration:</b><br>
        {self.conf_path}<br>
    • <b>Search history:</b><br>
        {self.hist_path}<br>
    <br>
    🔗 <b>More info and source code:</b><br>
    <a href="https://github.com/dmnmsc/kwebsearch">https://github.com/dmnmsc/kwebsearch</a>
    """
        )
        msg_box = QMessageBox(
            QMessageBox.Icon.Information, _("About kwebsearch"), about_text
        )
        msg_box.setTextFormat(Qt.TextFormat.RichText)
        open_button = msg_box.addButton(
            "🌐 Open website", QMessageBox.ButtonRole.AcceptRole
        )
        msg_box.addButton(QMessageBox.StandardButton.Close)
        msg_box.setDefaultButton(open_button)
        msg_box.exec()
        if msg_box.clickedButton() == open_button:
            webbrowser.open("https://github.com/dmnmsc/kwebsearch")
