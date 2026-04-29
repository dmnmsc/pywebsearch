import os
import gettext
import sys
from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import QMessageBox, QFileDialog
from pywebsearch.config import ConfigHandler
from pywebsearch.history import HistoryManager
from pywebsearch.backup import backup_files, restore_files
from pywebsearch.alias import AliasManager

_ = gettext.gettext


class SettingsManager:
    def __init__(self, pyweb_app, version="dev"):
        self.pyweb_app = pyweb_app
        self.dialogs = pyweb_app.dialogs
        self.version = version
        if self.pyweb_app.platform:
            self.config_dir, self.data_dir = self.pyweb_app.platform.get_platform_dirs()
        else:
            from platformdirs import user_config_dir, user_data_dir
            self.config_dir = user_config_dir(
                "pywebsearch", appauthor="dmnmsc", ensure_exists=True
            )
            self.data_dir = user_data_dir(
                "pywebsearch", appauthor="dmnmsc", ensure_exists=True
            )
        self.conf_path = os.path.join(self.config_dir, "pywebsearch.conf")
        self.hist_path = os.path.join(self.data_dir, "pywebsearch_history")
        self.backup_dir = os.path.join(self.data_dir, "backup")

        self.setup_directories()

        self.config = ConfigHandler(self.conf_path)
        self.history = HistoryManager(self.hist_path)
        self.pyweb_app.config = self.config
        self.pyweb_app.history = self.history
        self.pyweb_app.conf_path = self.conf_path
        self.pyweb_app.hist_path = self.hist_path
        self.pyweb_app.backup_dir = self.backup_dir
        self.aliases = self.config.get_aliases()
        self.pyweb_app.aliases = self.aliases
        self.pyweb_app.default_alias = self.config.get_value("default_alias")
        self.pyweb_app.default_browser = self.config.get_value("default_browser")
        self.pyweb_app.cmd_prefix = self.config.get_value("cmd_prefix") or ">"
        self.pyweb_app.alt_cmd_prefix = self.config.get_value("alt_cmd_prefix") or "@"
        self.pyweb_app.alt_browser = self.config.get_value("alt_browser")
        self.alias_manager = AliasManager(
            self.dialogs,
            self.conf_path,
            self.aliases,
            self.reload_config,
            self.pyweb_app.platform,
            self.config,
            self.pyweb_app.default_alias,
            self.pyweb_app.process_search,
            self.pyweb_app.duckduckgo_search,
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
            ConfigHandler(self.conf_path).create_default_config()
            self.dialogs.show_config_created(self.conf_path)

    def reload_config(self):
        self.config.load()
        self.aliases = self.config.get_aliases()
        self.pyweb_app.aliases = self.aliases
        self.pyweb_app.default_alias = self.config.get_value("default_alias")
        self.pyweb_app.default_browser = self.config.get_value("default_browser")
        self.pyweb_app.cmd_prefix = self.config.get_value("cmd_prefix") or ">"
        self.pyweb_app.alt_cmd_prefix = self.config.get_value("alt_cmd_prefix") or "@"
        self.pyweb_app.alt_browser = self.config.get_value("alt_browser")
        self.pyweb_app.reload_config()
        self.alias_manager.aliases = self.aliases

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
        while True:
            new_prefix = self.dialogs.get_input(
                _("Change URL prefix"),
                _(
                    f"Current symbol: {self.pyweb_app.cmd_prefix}\n\nEnter new prefix to open URLs directly:"
                ),
                text=self.pyweb_app.cmd_prefix,
                select_text=True,
            )

            # User cancelled
            if new_prefix is None:
                return

            # Validate empty or contains space
            if not new_prefix or " " in new_prefix:
                self.dialogs.show_message_box(
                    _("Invalid prefix. Please try again."),
                    _("Error"),
                    icon=QMessageBox.Icon.Warning,
                )
                continue

            # Check that it's not the same as alt_cmd_prefix
            if new_prefix == self.pyweb_app.alt_cmd_prefix:
                self.dialogs.show_message_box(
                    _(f"URL prefix cannot be the same as alternative prefix ({self.pyweb_app.alt_cmd_prefix})"),
                    _("Error"),
                    icon=QMessageBox.Icon.Warning,
                )
                continue

            # Valid prefix, save and exit
            self.config.set_value("cmd_prefix", new_prefix)
            self.dialogs.show_message_box(_("✅ Prefix updated to: ") + new_prefix)
            self.reload_config()
            break

    def set_default_browser(self):
        self.reload_config()
        current = self.pyweb_app.default_browser or ""
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

    def set_alt_browser(self):
        current = self.pyweb_app.alt_browser or ""
        new_browser = self.dialogs.get_input(
            _("Set alternative browser command"),
            _("Enter the alternative browser command with options (e.g. chromium --new-tab):"),
            text=current,
            select_text=True,
        )
        if new_browser is None:
            return
        self.config.set_value("alt_browser", new_browser)
        self.dialogs.show_message_box(_("✅ Alternative browser updated to: ") + new_browser)
        self.reload_config()

    def set_alt_cmd_prefix(self):
        current = self.pyweb_app.alt_cmd_prefix or "@"

        while True:
            new_prefix = self.dialogs.get_input(
                _("Change alternative command prefix"),
                _("Enter new symbol to use as alternative command prefix:"),
                text=current,
                select_text=True,
            )

            # User cancelled
            if new_prefix is None:
                return

            # Validate empty or contains space
            if not new_prefix or " " in new_prefix:
                self.dialogs.show_message_box(
                    _("Invalid prefix. Please try again."),
                    _("Error"),
                    icon=QMessageBox.Icon.Warning,
                )
                current = new_prefix  # Keep what user typed
                continue

            # Check that it's not the same as cmd_prefix
            if new_prefix == self.pyweb_app.cmd_prefix:
                self.dialogs.show_message_box(
                    _(f"Alternative prefix cannot be the same as URL prefix ({self.pyweb_app.cmd_prefix})"),
                    _("Error"),
                    icon=QMessageBox.Icon.Warning,
                )
                current = new_prefix  # Keep what user typed
                continue

            # Valid prefix, save and exit
            self.config.set_value("alt_cmd_prefix", new_prefix)
            self.dialogs.show_message_box(_("✅ Alternative command prefix updated to: ") + new_prefix)
            self.reload_config()
            break

    def backup_config(self):
        options_map = [
            (_("⚙️ Aliases (pywebsearch.conf)"), True),
            (_("🕘 History (pywebsearch_history)"), True),
            (_("📦 Both"), True),
        ]
        selection = self.dialogs.show_radio_list_dialog(
            _("Export configuration"), _("What do you want to export?"), options_map
        )
        if not selection:
            return
        selected_option = options_map[selection - 1][0]
        files_map = {
            _("⚙️ Aliases (pywebsearch.conf)"): [self.pyweb_app.conf_path],
            _("🕘 History (pywebsearch_history)"): [self.pyweb_app.hist_path],
            _("📦 Both"): [self.pyweb_app.conf_path, self.pyweb_app.hist_path],
        }
        messages_map = {
            _("⚙️ Aliases (pywebsearch.conf)"): "✅ Aliases exported at:",
            _("🕘 History (pywebsearch_history)"): "✅ History exported at:",
            _("📦 Both"): "✅ Aliases and history exported at:",
        }
        dest = backup_files(files_map[selected_option], self.pyweb_app.backup_dir)
        message = messages_map.get(selected_option, "✅ Backup created at:")
        self.dialogs.show_backup_created(dest, message)

    def restore_config(self):
        backups_dir = self.pyweb_app.backup_dir
        backups = sorted(
            (
                d
                for d in os.listdir(backups_dir)
                if d.startswith("20")
                and os.path.isdir(os.path.join(backups_dir, d))
            ),
            reverse=True,
        )
        if not backups:
            self.dialogs.show_message_box(
                _("❌ No backups found."), _("Error"), QMessageBox.Icon.Critical
            )
            return

        selected_files, _ignored = QFileDialog.getOpenFileNames(
            self.dialogs.parent,
            _("Select backup files to restore"),
            backups_dir,
            "Backup files (pywebsearch.conf pywebsearch_history);;All Files (*)",
            options=QFileDialog.Option.DontUseNativeDialog | QFileDialog.Option.ReadOnly,
        )
        if not selected_files:
            return

        restore_conf = False
        restore_hist = False

        for file_path in selected_files:
            base_name = os.path.basename(file_path)
            if base_name == "pywebsearch.conf":
                restore_conf = True
                conf_path = file_path
            elif base_name == "pywebsearch_history":
                restore_hist = True
                hist_path = file_path

        if not (restore_conf or restore_hist):
            self.dialogs.show_message_box(
                _("❌ No valid backup files selected."), _("Error"), QMessageBox.Icon.Critical
            )
            return

        if restore_conf:
            restore_files(os.path.dirname(conf_path), [self.pyweb_app.conf_path])
        if restore_hist:
            restore_files(os.path.dirname(hist_path), [self.pyweb_app.hist_path])

        messages = []
        if restore_conf:
            messages.append(_("✅ Aliases restored successfully"))
        if restore_hist:
            messages.append(_("✅ History restored successfully"))

        self.dialogs.show_message_box("\n".join(messages))

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
            self.pyweb_app.process_search(selected, history_manager=self.history)

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
            self.pyweb_app.open_direct_url(url)

    def import_browsers(self):
        use_deep_scan = False
        # On Windows, let the user explicitly choose scan method
        if sys.platform.startswith("win"):
            choice = self.dialogs.show_radio_list_dialog(
                "Choose browser scan method",
                "Select the scanning method to find extra browsers:",
                [
                    ("pybrowsers scan (better, but may miss some browsers)", True),  # First option
                    ("installed_browsers scan (just for fallback)", True),  # Second option fallback
                ],
            )
            if choice == 1:
                use_deep_scan = False  # pybrowsers scan (faster)
            elif choice == 2:
                use_deep_scan = True   # installed_browsers scan (deeper)
            else:
                # Cancel or closed dialog
                return
            new_browsers = self.pyweb_app.platform.import_extra_browsers(use_deep_scan)
        else:
            new_browsers = self.pyweb_app.platform.import_extra_browsers()

        if not new_browsers:
            self.dialogs.show_message_box("No new browsers found.")
            return

        chosen = self.dialogs.show_list_dialog(
            "Add browsers",
            "Select browsers to add to your configuration:",
            list(new_browsers)
        )
        if chosen:
            existing = self.config.get_value("extra_browsers").split(",")
            updated = set(existing) | {chosen}
            safe_updated = [b for b in updated if self.pyweb_app.platform.is_browser_name_safe(b)]
            self.config.set_value("extra_browsers", ",".join(safe_updated))
            self.dialogs.show_message_box("✅ Browsers added successfully.")

    def show_help(self):
        help_text = _(
            """
🧾 <b>Explore the web your way using PyWebSearch!</b>
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
<pre>
🔎 <b><i>Normal search:</i> Type any query to search the web.</b>
    → <i>Example: mechanical keyboard</i>
    → <i>Example: Linux file search tools</i>

🟢 <b><i>!bang:</i> Perform quick searches with DuckDuckGo aliases.</b>
    → <i>Example: !w solar energy</i>  (Wikipedia search)
    → <i>Example: !gh pywebsearch</i> (GitHub search)

🔎 <b><i>alias:query:</i> Use custom aliases defined by you.</b>
    → <i>Example: g:mechanical keyboard</i> (Google search)
    → <i>Example: w:Linux</i> (Wikipedia Search)

🌐 <b><i>>url:</i> Open a URL directly in your browser.</b>
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
<tr><td><b>_altbrowser</b></td><td>Set alternative browser</td></tr>
<tr><td><b>_history</b></td><td>View recent search history</td></tr>
<tr><td><b>_clear</b></td><td>Clear history</td></tr>
<tr><td><b>_prefix</b></td><td>Change symbol for opening URLs directly (e.g., &gt;)</td></tr>
<tr><td><b>_altprefix</b></td><td>Change symbol for launching the alternative browser (e.g., @)</td></tr>
<tr><td><b>_backup</b></td><td>Create backup of config and history</td></tr>
<tr><td><b>_restore</b></td><td>Restore existing backup</td></tr>
<tr><td><b>_help</b></td><td>Show this help</td></tr>
<tr><td><b>_about</b></td><td>About pywebsearch</td></tr>
<tr><td><b>_exit</b></td><td>Exit the program</td></tr>
</table>
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
"""
        )
        self.dialogs.show_rich_text_dialog(_("Help - PyWebSearch"), help_text)

    def about_info(self):
        about_text = _(
            f"""<h2 style="color:#2E86C1;">🛠️ pywebsearch <span style="font-size:22px; font-weight:bold; padding:3px 6px; border-radius:4px;">v{self.version}</span></h2>
    <br>
    📌 <b>What is pywebsearch?</b><br>
    A simple and practical tool to perform fast searches and open web pages using customizable aliases and !bangs, with a user-friendly GUI.<br><br>
    ⭐ <b>Main features:</b><br>
    • Quick alias searches<br>
    • <i>DuckDuckGo !bangs</i> integration for versatile searches<br>
    • Direct URL opening with configurable prefix<br>
    • Local search history auto saved<br>
    • Configuration and history backup and restore<br><br>
    📂 <b>Main files:</b><br>
    • <b>Alias configuration:</b><br>
    <a href="file://{self.conf_path}">{self.conf_path}</a><br><br>
    • <b>Search history:</b><br>
    <a href="file://{self.hist_path}">{self.hist_path}</a><br><br>
    🎨 <b>Icon credits:</b><br>
    <a href="https://www.svgrepo.com/svg/522651/search-globe">Search Globe SVG Vector 2</a> by 
    <a href="https://www.svgrepo.com/author/Vlad%20Cristea/">Vlad Cristea</a>
    distributed under <a href="https://www.svgrepo.com/page/licensing/#CC%20Attribution">CC Attribution License</a><br><br>
    🔗 <b>More info and source code:</b><br>
    <a href="https://github.com/dmnmsc/pywebsearch">https://github.com/dmnmsc/pywebsearch</a>
    """
        )

        from pywebsearch.main import load_icon
        from PyQt6.QtGui import QIcon
        self.dialogs.show_rich_text_dialog(
            title=_("About pywebsearch"),
            text=about_text,
            icon=QIcon(load_icon()),
            buttons_callbacks=[
                (_("🌐 Open website"), lambda: self.pyweb_app.launch_url("https://github.com/dmnmsc/pywebsearch"))
            ],
        )
