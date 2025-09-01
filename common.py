#!/usr/bin/env python3
import sys
import os
import subprocess
import re
import webbrowser
import shutil
from urllib.parse import quote_plus
from datetime import datetime
from platformdirs import user_config_dir, user_data_dir
import platform
import gettext
from PyQt6.QtWidgets import (
    QInputDialog,
    QMessageBox,
    QComboBox,
    QDialog,
    QVBoxLayout,
    QLabel,
    QRadioButton,
    QDialogButtonBox,
    QLineEdit,
    QListWidget,
    QListWidgetItem,
)

from PyQt6.QtCore import Qt

VERSION = "3.4"

# Setup gettext translations
base_dir = os.path.dirname(os.path.abspath(sys.argv[0]))
localedir = os.path.join(base_dir, "locales")
translation = gettext.translation("kwebsearch", localedir, fallback=True)
translation.install()
_ = translation.gettext

script_dir = os.path.dirname(os.path.abspath(__file__))
icon_path = os.path.join(script_dir, "kwebsearch.ico")

VERBOSE = False  # Will be set by main.py


class Dialogs:
    def __init__(self, parent=None):
        self.parent = parent

    def show_message_box(
        self, text, title="KWebSearch", icon=QMessageBox.Icon.Information
    ):
        msg = QMessageBox(self.parent)
        msg.setIcon(icon)
        msg.setWindowTitle(title)
        msg.setText(text)
        msg.setStandardButtons(QMessageBox.StandardButton.Ok)
        msg.exec()

    def show_yes_no_box(
        self, text, title="KWebSearch", default_button=QMessageBox.StandardButton.No
    ):
        reply = QMessageBox.question(
            self.parent,
            title,
            text,
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            default_button,
        )
        return reply == QMessageBox.StandardButton.Yes

    def get_input(self, title, label, text="", select_text=False):
        input_dialog = QInputDialog(self.parent)
        input_dialog.setWindowFlags(
            input_dialog.windowFlags() & ~Qt.WindowType.WindowContextHelpButtonHint
        )
        input_dialog.setWindowTitle(title)
        input_dialog.setLabelText(label)
        input_dialog.setTextValue(text)
        if select_text:
            input_dialog.findChild(QLineEdit).selectAll()
        if input_dialog.exec():
            return input_dialog.textValue()
        return None

    def show_list_dialog(self, title, label, items, radio=False):
        dialog = QDialog(self.parent)
        dialog.setWindowTitle(title)
        layout = QVBoxLayout()
        layout.addWidget(QLabel(label))
        if radio:
            radio_buttons = []
            for i, (text, checked) in enumerate(items):
                radio_button = QRadioButton(text)
                radio_button.setChecked(checked)
                layout.addWidget(radio_button)
                radio_buttons.append((str(i + 1), radio_button))
        else:
            combo = QComboBox()
            combo.addItems(items)
            layout.addWidget(combo)
        buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel
        )
        buttons.accepted.connect(dialog.accept)
        buttons.rejected.connect(dialog.reject)
        layout.addWidget(buttons)
        dialog.setLayout(layout)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            if radio:
                for val, button in radio_buttons:
                    if button.isChecked():
                        return val
            else:
                return combo.currentText()
        return None

    def show_searchable_list_dialog(self, title, label, items):
        dialog = QDialog(self.parent)
        dialog.setWindowTitle(title)
        layout = QVBoxLayout()
        layout.addWidget(QLabel(label))
        search_field = QLineEdit()
        search_field.setPlaceholderText(_("🔍 Type to filter..."))
        layout.addWidget(search_field)
        list_widget = QListWidget()
        for item in items:
            QListWidgetItem(item, list_widget)
        layout.addWidget(list_widget)
        buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel
        )
        buttons.accepted.connect(dialog.accept)
        buttons.rejected.connect(dialog.reject)
        layout.addWidget(buttons)
        dialog.setLayout(layout)

        def filter_items(text):
            for i in range(list_widget.count()):
                item = list_widget.item(i)
                item.setHidden(text.lower() not in item.text().lower())

        search_field.textChanged.connect(filter_items)

        if dialog.exec() == QDialog.DialogCode.Accepted:
            current_item = list_widget.currentItem()
            if current_item:
                return current_item.text()
        return None

    def show_radio_list_dialog(self, title, label, items):
        dialog = QDialog(self.parent)
        dialog.setWindowTitle(title)
        layout = QVBoxLayout()
        layout.addWidget(QLabel(label))
        radio_buttons = []
        for text, enabled in items:
            radio = QRadioButton(text)
            radio.setEnabled(enabled)
            radio_buttons.append(radio)
            layout.addWidget(radio)
        for radio in radio_buttons:
            if radio.isEnabled():
                radio.setChecked(True)
                break
        buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel
        )
        buttons.accepted.connect(dialog.accept)
        buttons.rejected.connect(dialog.reject)
        layout.addWidget(buttons)
        dialog.setLayout(layout)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            for i, radio in enumerate(radio_buttons):
                if radio.isChecked():
                    return i + 1
        return None


class KWebSearchApp:
    def __init__(self, platform_module=None):
        # platform_module: injected module for platform specific functions (linux.py/windows.py)
        self.platform = platform_module

        if self.platform:
            self.config_dir, self.data_dir = self.platform.get_platform_dirs()
        else:
            # fallback generic Linux-style dirs
            self.config_dir = user_config_dir(
                "kwebsearch", appauthor="dmnmsc", ensure_exists=True
            )
            self.data_dir = user_data_dir(
                "kwebsearch", appauthor="dmnmsc", ensure_exists=True
            )

        self.conf = os.path.join(self.config_dir, "kwebsearch.conf")
        self.hist = os.path.join(self.data_dir, "kwebsearch_history")
        self.backup_dir = os.path.join(self.data_dir, "backup")

        self.aliases = {}
        self.default_browser = ""
        self.default_alias = ""
        self.cmd_prefix = ">"
        self.dialogs = Dialogs()

        self.setup_directories()
        self.load_config()

    def setup_directories(self):
        os.makedirs(self.config_dir, exist_ok=True)
        os.makedirs(self.data_dir, exist_ok=True)
        os.makedirs(self.backup_dir, exist_ok=True)
        if not os.path.exists(self.hist):
            open(self.hist, "a").close()
        if not os.path.exists(self.conf):
            self.create_default_config()

    def create_default_config(self):
        with open(self.conf, "w", encoding="utf-8") as f:
            f.write(
                _(
                    """# 🧠 Default alias (if left empty, DuckDuckGo via !bangs will be used)
default_alias=""

# 🌐 Default browser (firefox, chromium, brave, google-chrome...)
# Leave empty to use system default
default_browser=""

# 🚀 Prefix to open URLs directly (e.g., >github.com)
# You can change to ~, @, ^, ::, >, etc.
cmd_prefix=">"

# 🔎 Custom aliases in alias=URL-or-command format #comment
g="https://www.google.com/search?q=$query" #Google
i="https://www.google.com/search?tbm=isch&q=$query" #Google Images
y="https://www.youtube.com/results?search_query=$query" #YouTube
w="https://en.wikipedia.org/wiki/Special:Search?search=$query" #Wikipedia (EN)
p="https://www.perplexity.ai/search?q=$query" #Perplexity.ai
d="https://www.wordreference.com/definition/$query" #English dictionary
trans="https://translate.google.com/?sl=auto&tl=es&text=$query" #Google Translate
gh="https://github.com/search?q=$query&type=repositories" #GitHub
gl="https://gitlab.com/search?search=$query" #GitLab
so="https://stackoverflow.com/search?q=$query" #Stack Overflow
r="https://www.reddit.com/search?q=$query" #Reddit

#Example of external browser with flags:
.y="chromium --incognito https://www.youtube.com/results?search_query=$query" #YouTube (incognito)
"""
                )
            )
        self.dialogs.show_message_box(_("✅ Alias file created at:\n") + self.conf)

    def load_config(self):
        self.aliases.clear()
        try:
            with open(self.conf, "r", encoding="utf-8") as f:
                for line in f:
                    line = line.strip()
                    if line.startswith("default_alias="):
                        self.default_alias = line.split("=", 1)[1].strip().strip('"')
                    elif line.startswith("cmd_prefix="):
                        self.cmd_prefix = line.split("=", 1)[1].strip().strip('"')
                    elif line.startswith("default_browser="):
                        self.default_browser = line.split("=", 1)[1].strip().strip('"')
                    elif re.match(r"^[^#].*=", line):
                        match = re.match(r"^([^=]+)=(.*?)(?:#\s*(.*))?$", line)
                        if match:
                            key, cmd, desc = match.groups()
                            self.aliases[key.strip()] = {
                                "cmd": cmd.strip().strip('"'),
                                "desc": desc.strip() if desc else "",
                            }
        except FileNotFoundError:
            self.dialogs.show_message_box(
                _("❌ Error: Configuration file not found."),
                _("Error"),
                QMessageBox.Icon.Critical,
            )
            sys.exit(1)

    def is_linux(self):
        return platform.system() == "Linux"

    def launch_url(self, url):
        if self.platform:
            try:
                if not self.is_linux() and self.default_browser:
                    # If not Linux, use platform-specific launch (likely Windows)
                    self.platform.launch_url(url, verbose=VERBOSE)
                else:
                    # For Linux and others
                    self.platform.launch_url(url, verbose=VERBOSE)
                return
            except Exception as e:
                if VERBOSE:
                    print(f"❌ Platform-specific launch_url failed: {e}")
        if VERBOSE:
            print(f"🌐 Fallback: opening URL with webbrowser.open: {url}")
        import webbrowser
        webbrowser.open(url, new=2)

    def open_with_browser(self, url):
        self.launch_url(url)

    def open_direct_url(self, url):
        if not re.match(r"^[a-zA-Z]+://", url):
            url = f"https://{url}"
        print(_("🌐 Opening direct URL:"), url)
        self.launch_url(url)

    def duckduckgo_search(self, query):
        print(_("🔎 Performing DuckDuckGo search for"), f'"{query}"')
        url = f"https://duckduckgo.com/?q={quote_plus(query)}"
        self.launch_url(url)

    def open_cmd(self, *args):
        if not args:
            return
        prog = args[0]
        known_browsers = [
            "xdg-open",
            "firefox",
            "firefoxpwa",
            "chromium",
            "google-chrome",
            "brave",
            "opera",
            "lynx",
            "w3m",
            "links",
        ]
        if prog in known_browsers:
            url = args[-1]
            print(f"🌐 Opening URL via {prog}: {url}")
            webbrowser.open(url, new=2)
            return
        if VERBOSE:
            print(f"⚠️ Running external command: {' '.join(args)}")
            subprocess.run(args)
        else:
            subprocess.Popen(
                args,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
                start_new_session=True,
            )

    # Platform-dependent alias file editing delegates to platform module
    def edit_alias(self):
        if self.platform:
            self.platform.open_config_file(self.conf, verbose=VERBOSE)
        else:
            # fallback to no action, or add simple fallback here
            self.dialogs.show_message_box(
                _("❌ Could not open configuration file."),
                _("Error"),
                QMessageBox.Icon.Critical,
            )

    def set_default_browser(self):
        self.load_config()
        current = self.default_browser or ""
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
        with open(self.conf, "r+", encoding="utf-8") as f:
            content = f.read()
            if re.search(r"^default_browser=.*$", content, flags=re.MULTILINE):
                content = re.sub(
                    r"^default_browser=.*$",
                    f'default_browser="{new_browser}"',
                    content,
                    flags=re.MULTILINE,
                )
            else:
                content += f'\ndefault_browser="{new_browser}"\n'
            f.seek(0)
            f.truncate()
            f.write(content)
        self.dialogs.show_message_box(
            _("✅ Default browser updated to: ") + new_browser
        )
        self.load_config()

    def show_aliases(self):
        self.load_config()
        options = [
            _("DuckDuckGo ")
            + (_("🟢 (default)") if not self.default_alias else _("(default)"))
        ]
        keys = [""]
        descs = [_("DuckDuckGo")]
        for key, value in self.aliases.items():
            desc = value["desc"]
            if key == self.default_alias:
                desc += _(" 🟢 (current)")
            options.append(f"{desc} ({key})")
            keys.append(key)
            descs.append(desc)
        sel = self.dialogs.show_list_dialog(
            _("Available aliases"), _("Select an alias:"), options
        )
        if sel is None:
            return
        key = keys[options.index(sel)]
        desc = descs[options.index(sel)]
        query = self.dialogs.get_input(desc, _("Type your query:"))
        if query is None:
            return
        if key:
            self.process_search(f"{key}:{query}")
        else:
            self.duckduckgo_search(query)

    def create_alias(self):
        self.load_config()
        key = ""
        desc = ""
        template = ""
        while True:
            key = self.dialogs.get_input(
                _("Alias key (no spaces or parentheses):"), _("🔑 Alias key:"), text=key
            )
            if key is None:
                return
            key_sanitized = re.sub(r"[^a-zA-Z0-9_.@,+-]", "", key).strip()
            if not key_sanitized or key_sanitized in self.aliases:
                msg = (
                    _("❌ Key is empty or contains invalid characters.")
                    if not key_sanitized
                    else f"❌ {_('The key')} '{key_sanitized}' {_('already exists in the alias file.')}"
                )
                self.dialogs.show_message_box(
                    msg, _("Error"), QMessageBox.Icon.Critical
                )
                continue
            key = key_sanitized
            break
        while True:
            desc = self.dialogs.get_input(
                _(f"Description for '{key}':"), _("📘 Description:"), text=desc
            )
            if not desc:
                self.dialogs.show_message_box(
                    _("❌ Description cannot be empty."),
                    _("Error"),
                    QMessageBox.Icon.Critical,
                )
                continue
            break
        while True:
            template_text = (
                _("⚙️ Enter the URL template with $query\n\n")
                + _("Examples:\n")
                + "- https://example.com?q=$query\n"
                + "- firefox https://example.com?q=$query\n"
                + "- chromium --incognito https://example.com?q=$query"
            )
            template = self.dialogs.get_input(
                _(f"URL template for '{key}':"), template_text, text=template
            )
            if template is None:
                return
            if not template or "$query" not in template:
                msg = (
                    _("❌ Template cannot be empty.")
                    if not template
                    else _("❌ Missing placeholder $query in the template.")
                )
                self.dialogs.show_message_box(
                    msg, _("Error"), QMessageBox.Icon.Critical
                )
                continue
            break
        if self.dialogs.show_yes_no_box(
            _(f'🔍 Preview:\n\n{key}="{template}" # {desc}\n\nSave this alias?'),
            default_button=QMessageBox.StandardButton.Yes,
        ):
            with open(self.conf, "a", encoding="utf-8") as f:
                f.write(f'\n{key}="{template}" # {desc}\n')
            self.dialogs.show_message_box(_("✅ Alias saved successfully: ") + key)
            self.load_config()

    def set_default_alias(self):
        self.load_config()
        options = [f"{v['desc']} ({k})" for k, v in self.aliases.items()]
        keys = list(self.aliases.keys())
        options.append(_("🧹 Reset default alias (DuckDuckGo)"))
        keys.append("reset")
        sel = self.dialogs.show_list_dialog(
            _("Default alias"), _("Select a default alias:"), options
        )
        if sel is None:
            return
        key = keys[options.index(sel)]
        if key == "reset":
            self.reset_default_alias()
            return
        with open(self.conf, "r+", encoding="utf-8") as f:
            content = f.read()
            f.seek(0)
            f.truncate()
            f.write(
                re.sub(
                    r"^default_alias=.*$",
                    f'default_alias="{key}"',
                    content,
                    flags=re.MULTILINE,
                )
            )
        self.dialogs.show_message_box(
            _("✅ Default alias updated to: ") + self.aliases[key]["desc"]
        )
        self.load_config()

    def reset_default_alias(self):
        with open(self.conf, "r+", encoding="utf-8") as f:
            content = f.read()
            f.seek(0)
            f.truncate()
            f.write(
                re.sub(
                    r"^default_alias=.*$",
                    'default_alias=""',
                    content,
                    flags=re.MULTILINE,
                )
            )
        self.dialogs.show_message_box(_("🔄 Default alias reset to DuckDuckGo"))
        self.load_config()

    def view_history(self):
        if not os.path.getsize(self.hist):
            self.dialogs.show_message_box(_("ℹ️ No search history available yet."))
            return
        with open(self.hist, "r", encoding="utf-8") as f:
            history = [line.strip() for line in f if line.strip()]
        if not history:
            self.dialogs.show_message_box(_("ℹ️ No search history available yet."))
            return
        history.reverse()
        selected = self.dialogs.show_searchable_list_dialog(
            _("Search history"), _("Select a previous search:"), history
        )
        if selected:
            self.process_search(selected)

    def clear_history(self):
        if self.dialogs.show_yes_no_box(
            _("Are you sure you want to clear the search history?")
        ):
            open(self.hist, "w", encoding="utf-8").close()
            self.dialogs.show_message_box(_("✅ Search history cleared successfully."))

    def open_url_dialog(self):
        url = self.dialogs.get_input(
            _("Enter the URL to open:"),
            _("Enter the URL to open (e.g., example.com or https://example.com):"),
        )
        if url:
            self.open_direct_url(url)

    def set_prefix(self):
        new_prefix = self.dialogs.get_input(
            _("Change URL prefix"),
            _(
                f"Current symbol: {self.cmd_prefix}\n\nEnter new prefix to open URLs directly:"
            ),
            text=self.cmd_prefix,
            select_text=True,
        )
        if new_prefix is None or not new_prefix or " " in new_prefix:
            self.dialogs.show_message_box(
                _("Invalid prefix. No changes made."),
                _("Error"),
                QMessageBox.Icon.Warning,
            )
            return
        with open(self.conf, "r+", encoding="utf-8") as f:
            content = f.read()
            f.seek(0)
            f.truncate()
            f.write(
                re.sub(
                    r"^cmd_prefix=.*$",
                    f'cmd_prefix="{new_prefix}"',
                    content,
                    flags=re.MULTILINE,
                )
            )
        self.dialogs.show_message_box(_("✅ Prefix updated to: ") + new_prefix)
        self.load_config()

    def backup_config(self):
        options_map = [
            (_("⚙️ Aliases (kwebsearch.conf)"), True),
            (_("🕘 History (kwebsearch_history)"), True),
            (_("📦 Both"), True),
        ]
        selection = self.dialogs.show_radio_list_dialog(
            _("Export configuration"),
            _("What do you want to export?"),
            options_map,
        )
        if not selection:
            return
        selected_option = options_map[selection - 1][0]
        files_map = {
            _("⚙️ Aliases (kwebsearch.conf)"): [self.conf],
            _("🕘 History (kwebsearch_history)"): [self.hist],
            _("📦 Both"): [self.conf, self.hist],
        }
        timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
        file_names = [
            os.path.basename(f).replace("kwebsearch", "").replace(".", "_")
            for f in files_map[selected_option]
        ]
        dest_name = f"{timestamp}_kwebsearch_backup_{'_and_'.join(file_names)}"
        dest = os.path.join(self.backup_dir, dest_name)
        os.makedirs(dest, exist_ok=True)
        for file_path in files_map[selected_option]:
            shutil.copy2(file_path, dest)
        self.dialogs.show_message_box(_("✅ Aliases and history exported in:\n") + dest)

    def restore_config(self):
        backups = sorted(
            [
                d
                for d in os.listdir(self.backup_dir)
                if d.startswith("20")
                and os.path.isdir(os.path.join(self.backup_dir, d))
            ],
            reverse=True,
        )
        if not backups:
            self.dialogs.show_message_box(
                _("❌ No backups found."), _("Error"), QMessageBox.Icon.Critical
            )
            return
        selected_backup_name = self.dialogs.show_list_dialog(
            _("Restore configuration"), _("Select backup to restore:"), backups
        )
        if not selected_backup_name:
            return
        full_path = os.path.join(self.backup_dir, selected_backup_name)
        has_conf = os.path.exists(os.path.join(full_path, "kwebsearch.conf"))
        has_hist = os.path.exists(os.path.join(full_path, "kwebsearch_history"))
        if not has_conf and not has_hist:
            self.dialogs.show_message_box(
                _("❌ Selected backup does not contain valid files."),
                _("Error"),
                QMessageBox.Icon.Critical,
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
            shutil.copy2(os.path.join(full_path, "kwebsearch.conf"), self.conf)
            self.dialogs.show_message_box(_("✅ Aliases restored successfully"))
        elif selection == 2 and has_hist:
            shutil.copy2(os.path.join(full_path, "kwebsearch_history"), self.hist)
            self.dialogs.show_message_box(_("✅ History restored successfully"))
        elif selection == 3 and has_conf and has_hist:
            shutil.copy2(os.path.join(full_path, "kwebsearch.conf"), self.conf)
            shutil.copy2(os.path.join(full_path, "kwebsearch_history"), self.hist)
            self.dialogs.show_message_box(
                _("✅ Aliases and history restored successfully")
            )

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
        self.dialogs.show_message_box(help_text, _("kwebsearch help"))

    def about_info(self):
        about_text = _(
            f"""<b>🛠️ kwebsearch - Custom web search tool</b><br>
Version: <b>{VERSION}</b><br>
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
    {self.conf}<br>
• <b>Search history:</b><br>
    {self.hist}<br>
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

    def execute_search(self, key, query):
        alias_data = self.aliases.get(key)
        if not alias_data:
            print(f"🔎 Alias not found: {key}, falling back to DuckDuckGo")
            self.duckduckgo_search(query)
            return

        description = alias_data.get("desc", "")
        desc_text = (
            f"#{description} alias ({key}:)" if description else f"alias ({key}:)"
        )
        cmd_template = alias_data["cmd"].strip('"')
        query_encoded = quote_plus(query)
        cmd_template = re.sub(r"\$query", query_encoded, cmd_template)
        cmd_array = cmd_template.split()
        known_browsers = {
            "firefox",
            "chromium",
            "brave",
            "google-chrome",
            "opera",
            "chrome",
        }

        # If first token is a known browser, launch the command directly
        if cmd_array and cmd_array[0] in known_browsers:
            print(
                f'🔎 Performing search for "{query}" using {desc_text} with custom browser command:'
            )
            print(f"⚙️ {cmd_template}")
            try:
                if VERBOSE:
                    subprocess.Popen(cmd_template, shell=True)
                else:
                    subprocess.Popen(
                        cmd_template,
                        shell=True,
                        stdout=subprocess.DEVNULL,
                        stderr=subprocess.DEVNULL,
                        start_new_session=True,
                    )
            except Exception as e:
                print(f"❌ Error executing command: {e}")
                self.duckduckgo_search(query)
            return

        # If the command is a URL, open with launch_url
        if cmd_template.startswith(("http://", "https://")):
            print(f'🔎 Performing search for "{query}" using {desc_text} via URL:')
            print(f"🌐 {cmd_template}")
            self.launch_url(cmd_template)
            return

        supported_browsers = ["firefox", "chrome", "chromium", "safari", "opera"]
        browser_name = cmd_array[0] if cmd_array else ""

        # If browser with simple URL, use webbrowser module to open
        if browser_name in supported_browsers and len(cmd_array) == 2:
            url = cmd_array[1]
            print(
                f"🔎 Performing search for \"{query}\" using {desc_text} with browser '{browser_name}': {url}"
            )
            try:
                browser = webbrowser.get(browser_name)
                browser.open(url, new=2)
                return
            except webbrowser.Error:
                print(f"Browser '{browser_name}' not found. Opening default browser.")
                webbrowser.open(url, new=2)
                return

        # If platform exposes launch_alias_command (Windows), call it for complex command launching
        if self.platform and hasattr(self.platform, "launch_alias_command"):
            print(f"⚙️ Executing complex alias command for {desc_text}: {cmd_template}")
            try:
                launched = self.platform.launch_alias_command(
                    cmd_template, verbose=VERBOSE
                )
                if not launched:
                    print(
                        "❌ Failed to launch alias command, falling back to DuckDuckGo"
                    )
                    self.duckduckgo_search(query)
                return
            except Exception as e:
                print(f"❌ Error launching alias command: {e}")
                self.duckduckgo_search(query)
                return

        # Fallback: generic subprocess launch
        try:
            if VERBOSE:
                print(f"⚙️ Executing complex command for {desc_text}: {cmd_template}")
                subprocess.Popen(cmd_template, shell=True)
            else:
                subprocess.Popen(
                    cmd_template,
                    shell=True,
                    stdout=subprocess.DEVNULL,
                    stderr=subprocess.DEVNULL,
                    start_new_session=True,
                )
        except Exception as e:
            print(f"❌ Error executing command: {e}")
            self.duckduckgo_search(query)

    def process_search(self, input_str):
        self.load_config()
        with open(self.hist, "a+", encoding="utf-8") as f:
            f.seek(0)
            if input_str not in f.read().splitlines():
                f.write(input_str + "\n")
        if input_str.startswith(self.cmd_prefix):
            self.open_direct_url(input_str[len(self.cmd_prefix):])
        elif ":" in input_str:
            key, query = input_str.split(":", 1)
            if key.strip() in self.aliases:
                self.execute_search(key.strip(), query.strip())
            else:
                self.duckduckgo_search(input_str)
        else:
            if self.default_alias:
                self.execute_search(self.default_alias, input_str)
            else:
                self.duckduckgo_search(input_str)
