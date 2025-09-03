import os


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
        for line in self.lines:
            line = line.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            key, rest = line.split("=", 1)
            key = key.strip()
            if key.startswith(".") or not key[0].isalnum():
                continue
            cmd_part = rest.split("#")[0].strip().strip('"')
            desc_part = ""
            if "#" in rest:
                desc_part = rest.split("#", 1)[1].strip()
            aliases[key] = {"cmd": cmd_part, "desc": desc_part}
        return aliases
