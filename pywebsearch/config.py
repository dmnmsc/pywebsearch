import os
import gettext

_ = gettext.gettext


class ConfigHandler:
    def __init__(self, config_file):
        self.config_file = config_file
        self.lines = []
        self.load()

    def load(self):
        if not os.path.exists(self.config_file):
            self.lines = []
            return
        with open(self.config_file, "r", encoding="utf-8") as f:
            self.lines = f.readlines()

    def save(self):
        with open(self.config_file, "w", encoding="utf-8") as f:
            f.writelines(self.lines)

    def get_value(self, key):
        for line in self.lines:
            if line.startswith(f"{key}="):
                return line.split("=", 1)[1].strip().strip('"')
        return ""

    def set_value(self, key, value):
        updated = False
        for i, line in enumerate(self.lines):
            if line.startswith(f"{key}="):
                self.lines[i] = f'{key}="{value}"\n'
                updated = True
                break
        if not updated:
            self.lines.append(f'{key}="{value}"\n')
        self.save()

    def get_aliases(self):
        aliases = {}
        config_keys = {"default_alias", "default_browser", "cmd_prefix", "extra_browsers", "alt_browser", "alt_cmd_prefix"}
        for line in self.lines:
            line = line.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            key, rest = line.split("=", 1)
            key = key.strip()
            # Omit config keys and malformed alias names
            if key in config_keys:
                continue
            cmd_part = rest.split("#")[0].strip().strip('"')
            desc_part = ""
            if "#" in rest:
                desc_part = rest.split("#", 1)[1].strip()
            aliases[key] = {"cmd": cmd_part, "desc": desc_part}
        return aliases

    def get_extra_browsers(self):
        value = self.get_value("extra_browsers")
        return [v.strip() for v in value.split(",") if v.strip()]
    # Already have set_value -- store as comma-separated string.

    def create_default_config(self):
        """
        Create a default configuration file with config keys at the top,
        aliases clearly separated, and 'extra_browsers' present.
        """
        if os.path.exists(self.config_file):
            return
        with open(self.config_file, "w", encoding="utf-8") as f:
            f.write(
                _(
                    """# 🧠 Default alias (if left empty, DuckDuckGo via !bangs will be used)
default_alias=""

# 🌐 Default and alt browser (firefox, chromium, brave, google-chrome...)
# Leave empty to use system default
default_browser=""
alt_browser=""

# 🚀 Prefix to open URLs directly (e.g., >github.com)
# You can change to ~, @, ^, ::, >, etc.
cmd_prefix=">"
alt_cmd_prefix="@"

# 🧭 Extra imported browsers (comma-separated)
extra_browsers=""

# 🔎 Custom aliases in alias=URL-or-command format #comment
g="https://www.google.com/search?q=$query" #Google
i="https://www.google.com/search?tbm=isch&q=$query" #Google Images
y="https://www.youtube.com/results?search_query=$query" #YouTube
w="https://en.wikipedia.org/wiki/Special:Search?search=$query" #Wikipedia (EN)
p="https://www.perplexity.ai/search?q=$query" #Perplexity.ai
d="https://www.wordreference.com/definition/$query" #English dictionary
trans="https://translate.google.com/?sl=auto&tl=es&text=$query" #Google Translate
gh="https://github.com/search?q=$query&type=repositories" #GitHub
gl="https://gitlab.com/search?search=+$query" #GitLab
so="https://stackoverflow.com/search?q=$query" #Stack Overflow
r="https://www.reddit.com/search?q=$query" #Reddit

#Example of external browser with flags (URL between ' '):
.y="chromium --incognito 'https://www.youtube.com/results?search_query=$query'" #YouTube (incognito)
"""
                )
            )
