#!/usr/bin/env python3
import os
import svgwrite

# Emojis used in the menu with file names
emojis = {
    "browser": "🔵",
    "url_prefix": "🔗",
    "backup": "📤",
    "restore": "📥",
    "rocket": "🚀",
    "reload": "🔃",
    "alias": "📗",
    "history": "🕘",
    "clear": "🧹",
    "url": "🌐",
    "new_alias": "🆕",
    "edit": "✏️",
    "default_alias": "🟢",
    "reset_alias": "🔄",
    "help": "❓",
    "about": "ℹ️"
}

output_dir = "emoji_svgs"
os.makedirs(output_dir, exist_ok=True)

for name, emoji_char in emojis.items():
    dwg = svgwrite.Drawing(filename=os.path.join(output_dir, f"{name}.svg"), size=("64px", "64px"))
    # We add the emoji as a text in the center
    dwg.add(
        dwg.text(
            emoji_char,
            insert=("32px", "48px"),
            text_anchor="middle",
            font_size="48px",
            font_family="Segoe UI Emoji, Apple Color Emoji, Noto Color Emoji, sans-serif"
        )
    )
    dwg.save()
    print(f"Guardado {name}.svg")
