import re
import gettext
from PyQt6.QtWidgets import QMessageBox

_ = gettext.gettext


class AliasManager:
    def __init__(
        self,
        dialogs,
        conf_path,
        aliases,
        reload_func,
        platform_obj,
        config_obj,
        default_alias,
        process_search_func,
        duck_func,
        history_manager,
    ):
        self.dialogs = dialogs
        self.conf_path = conf_path
        self.aliases = aliases
        self.reload_config = reload_func
        self.platform = platform_obj
        self.config_obj = config_obj
        self.default_alias = default_alias
        self.process_search_func = process_search_func
        self.duck_func = duck_func
        self.history_manager = history_manager

    def show_aliases(self):
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
        sel = self.dialogs.show_searchable_list_dialog(
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
            self.process_search_func(
                f"{key}:{query}", history_manager=self.history_manager
            )
        else:
            self.duck_func(query)

    def create_alias(self):
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
                + "- firefox 'https://example.com?q=$query'\n"
                + "- chromium --incognito 'https://example.com?q=$query'"
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
            with open(self.conf_path, "a", encoding="utf-8") as f:  # antes self.conf
                f.write(f'\n{key}="{template}" # {desc}\n')
            self.dialogs.show_message_box(_("✅ Alias saved successfully: ") + key)
            self.reload_config()

    def edit_alias(self):
        config_path = self.conf_path
        if hasattr(self.platform, "open_config_file"):
            self.platform.open_config_file(config_path)
        else:
            self.dialogs.show_message_box(
                _("Manually edit the file at:\n") + config_path,
                _("Edit alias file"),
                icon=QMessageBox.Icon.Information,
            )

    def set_default_alias(self):
        options = [f"{v['desc']} ({k})" for k, v in self.aliases.items()]
        keys = list(self.aliases.keys())
        options.append(_("🧹 Reset default alias (DuckDuckGo)"))
        keys.append("reset")
        sel = self.dialogs.show_searchable_list_dialog(
            _("Default alias"), _("Select a default alias:"), options
        )
        if sel is None:
            return
        key = keys[options.index(sel)]
        if key == "reset":
            self.reset_default_alias()
            return
        with open(self.conf_path, "r+", encoding="utf-8") as f:
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
        self.reload_config()

    def reset_default_alias(self):
        if self.dialogs.show_yes_no_box(
            _("Are you sure you want to reset the default alias to DuckDuckGo?")
        ):
            self.config_obj.set_value("default_alias", "")
            self.dialogs.show_message_box(_("🔄 Default alias reset to DuckDuckGo"))
            self.reload_config()
