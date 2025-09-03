import os
import shutil
from datetime import datetime


def backup_files(files, backup_dir):
    """
    Backup selected files to a timestamped directory with descriptive naming including 'pywebsearch'.
    """
    timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    labels_map = {
        ("kwebsearch.conf",): "aliases",
        ("kwebsearch_history",): "history",
        ("kwebsearch.conf", "kwebsearch_history"): "full",
    }
    filenames = tuple(sorted(os.path.basename(f) for f in files))
    label = labels_map.get(filenames, "custom")
    dest_name = f"{timestamp}_pywebsearch_{label}_backup"
    dest = os.path.join(backup_dir, dest_name)
    os.makedirs(dest, exist_ok=True)
    for f in files:
        shutil.copy2(f, dest)
    return dest


def restore_files(backup_path, targets):
    """
    Restore selected files from backup_path into their original locations
    """
    for f in targets:
        src = os.path.join(backup_path, os.path.basename(f))
        if os.path.exists(src):
            shutil.copy2(src, f)
