import os


class HistoryManager:
    def __init__(self, history_file):
        self.history_file = history_file
        if not os.path.exists(self.history_file):
            with open(self.history_file, "a", encoding="utf-8"):
                pass

    def read_history(self):
        if (
            not os.path.exists(self.history_file)
            or os.path.getsize(self.history_file) == 0
        ):
            return []
        with open(self.history_file, "r", encoding="utf-8") as f:
            return [line.strip() for line in f if line.strip()]

    def add_entry(self, entry):
        entry = entry.strip()
        if not entry:
            return
        history = self.read_history()
        if entry in history:
            return
        with open(self.history_file, "a", encoding="utf-8") as f:
            f.write(entry + "\n")

    def clear_history(self):
        with open(self.history_file, "w", encoding="utf-8") as f:
            f.truncate()
