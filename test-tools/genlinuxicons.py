#!/usr/bin/env python3

import os
import sys
import shutil
import subprocess
from cairosvg import svg2png

def generate_icons(svg_path: str, output_dir: str) -> list:
    sizes = [16, 24, 32, 48, 64, 96, 128, 256, 512]
    created_icons = []

    for size in sizes:
        size_folder = f"{size}x{size}"
        target_folder = os.path.join(output_dir, size_folder, "apps")
        os.makedirs(target_folder, exist_ok=True)

        # Generate PNG
        png_path = os.path.join(target_folder, "pywebsearch.png")
        svg2png(url=svg_path, write_to=png_path, output_width=size, output_height=size)
        created_icons.append(png_path)
        print(f"PNG icon generated: {png_path}")

        # Copy SVG into each size folder
        svg_target = os.path.join(target_folder, "pywebsearch.svg")
        shutil.copy(svg_path, svg_target)
        print(f"SVG copied to: {svg_target}")

    # Copy SVG to scalable/apps
    scalable_folder = os.path.join(output_dir, "scalable", "apps")
    os.makedirs(scalable_folder, exist_ok=True)
    scalable_svg_path = os.path.join(scalable_folder, "pywebsearch.svg")
    shutil.copy(svg_path, scalable_svg_path)
    print(f"SVG copied to: {scalable_svg_path}")

    return created_icons

def install_icons(temp_output: str):
    print("\nInstalling icons system-wide...")
    try:
        # Run system-level install as root
        subprocess.run([
            "sudo", "bash", "-c",
            f"cp -r {os.path.join(temp_output, '*')} /usr/share/icons/hicolor/ && "
            "gtk-update-icon-cache /usr/share/icons/hicolor"
        ], check=True)
        print("✅ Icons installed.")

        # Restart plasmashell as current user
        subprocess.run(["kquitapp6", "plasmashell"])
        subprocess.run(["kstart", "plasmashell"])
        print("🔄 Plasma shell restarted.")

    except subprocess.CalledProcessError as e:
        print(f"❌ Installation failed: {e}")
