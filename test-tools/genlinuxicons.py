#!/usr/bin/env python3

import os
import sys
import shutil
import subprocess
from cairosvg import svg2png

def generate_icons(svg_path: str, output_dir: str):
    sizes = [16, 24, 32, 48, 64, 96, 128, 256, 512]
    for size in sizes:
        size_folder = f"{size}x{size}"
        target_folder = os.path.join(output_dir, size_folder, "apps")
        os.makedirs(target_folder, exist_ok=True)

        # Generate PNG
        png_path = os.path.join(target_folder, "pywebsearch.png")
        svg2png(url=svg_path, write_to=png_path, output_width=size, output_height=size)
        print(f"PNG generated: {png_path}")

        # Copy SVG to same folder
        svg_target = os.path.join(target_folder, "pywebsearch.svg")
        shutil.copy(svg_path, svg_target)
        print(f"SVG copied to: {svg_target}")

    # Scalable svg copy to scalable/apps
    scalable_folder = os.path.join(output_dir, "scalable", "apps")
    os.makedirs(scalable_folder, exist_ok=True)
    scalable_svg_path = os.path.join(scalable_folder, "pywebsearch.svg")
    shutil.copy(svg_path, scalable_svg_path)
    print(f"Scalable SVG copied: {scalable_svg_path}")

def run_command_sudo(cmd):
    print(f"Running command: {' '.join(cmd)}")
    try:
        subprocess.run(['sudo'] + cmd, check=True)
        print("Command executed successfully")
    except subprocess.CalledProcessError as e:
        print(f"Error executing command {' '.join(cmd)}: {e}")
        sys.exit(1)

def install_icons(temp_dir):
    base_dir = "/usr/share/icons/hicolor"
    sizes = [16, 24, 32, 48, 64, 96, 128, 256, 512]
    for size in sizes:
        src = os.path.join(temp_dir, f"{size}x{size}")
        dst = os.path.join(base_dir, f"{size}x{size}")
        print(f"Copying icons from {src} to {dst}")
        run_command_sudo(['cp', '-r', src + '/.', dst])

    # Copy scalable folder
    scalable_src = os.path.join(temp_dir, "scalable")
    scalable_dst = os.path.join(base_dir, "scalable")
    print(f"Copying scalable icons from {scalable_src} to {scalable_dst}")
    run_command_sudo(['cp', '-r', scalable_src + '/.', scalable_dst])

    # Update icon cache and restart Plasma Shell
    run_command_sudo(['gtk-update-icon-cache', base_dir])
    subprocess.run(['kquitapp6', 'plasmashell'])
    subprocess.run(['kstart', 'plasmashell'])

if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: ./script_name.py path/to/icon.svg")
        sys.exit(1)

    svg_path = sys.argv[1]
    if not os.path.isfile(svg_path):
        print(f"SVG file does not exist: {svg_path}")
        sys.exit(1)

    temp_dir = "/tmp/pywebsearch_icons"
    print("Generating icons...")
    generate_icons(svg_path, temp_dir)
    print("Installing icons...")
    install_icons(temp_dir)
    print("Icon installation complete.")
