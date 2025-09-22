#!/usr/bin/env python3
import subprocess
import sys
import os

def export_png(svg_file, size):
    output_file = f"icon-{size}.png"
    command = [
        "inkscape",
        svg_file,
        f"--export-type=png",
        f"--export-filename={output_file}",
        f"--export-width={size}",
        f"--export-height={size}"
    ]
    print(f"Exporting {output_file}...")
    subprocess.run(command, check=True)
    return output_file

def create_ico(png_files):
    ico_file = "pywebsearch.ico"
    command = ["magick"] + png_files + [ico_file]
    print(f"Creating {ico_file}...")
    subprocess.run(command, check=True)

def main():
    if len(sys.argv) != 2:
        print(f"Usage: {os.path.basename(sys.argv[0])} path/to/icon.svg")
        sys.exit(1)
    svg_file = sys.argv[1]
    if not os.path.isfile(svg_file):
        print(f"File not found: {svg_file}")
        sys.exit(1)

    sizes = [16, 32, 48, 64, 128, 256]
    png_files = []
    for size in sizes:
        png_files.append(export_png(svg_file, size))

    create_ico(png_files)
    print("Process complete.")

if __name__ == "__main__":
    main()
