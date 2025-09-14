#!/usr/bin/env python3

import os
import sys
from PIL import Image

def create_icons(png_path, output_folder):
    sizes = [(16, 16), (24, 24), (48, 48), (64, 64)]
    icons_created = []
    for size in sizes:
        image = Image.open(png_path)
        resized_image = image.resize(size, Image.LANCZOS)
        size_folder = f"{size[0]}x{size[1]}"
        folder = os.path.join(output_folder, size_folder, "apps")
        os.makedirs(folder, exist_ok=True)
        icon_name = os.path.basename(png_path)
        destination = os.path.join(folder, icon_name)
        resized_image.save(destination)
        icons_created.append(destination)
        print(f"Icon created in {destination}")
    return icons_created

if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: ./script_name.py path/to/icon.png")
        sys.exit(1)
    icon_path = sys.argv[1]
    temp_folder = "/tmp/pywebsearch_icons"
    create_icons(icon_path, temp_folder)

    print("\nTo install the icons system-wide, run the following commands with root permissions:")
    print(f"sudo cp -r {os.path.join(temp_folder, '*')} /usr/share/icons/hicolor/")
    print("sudo gtk-update-icon-cache /usr/share/icons/hicolor")
