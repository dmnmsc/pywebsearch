import os
import requests

# Dictionary with emoji name and Unicode code
emojis = {
    "browser": "1f535",
    "url_prefix": "1f4ce",
    "backup": "1f4e4",
    "restore": "1f4e5",
    "rocket": "1f680",
    "reload": "1f503",
    "alias": "1f4d7",
    "history": "1f559",
    "clear": "1f9f9",
    "url": "1f310",
    "new_alias": "1f195",
    "edit": "270f",
    "default_alias": "1f7e2",
    "reset_alias": "1f504",
    "help": "2753",
    "about": "2139"
}

# Output folder
output_dir = "noto_svgs"
os.makedirs(output_dir, exist_ok=True)

# Base URL of the Noto Emoji repository
base_url = "https://raw.githubusercontent.com/googlefonts/noto-emoji/main/svg"

for name, code in emojis.items():
    url = f"{base_url}/emoji_u{code}.svg"
    response = requests.get(url)
    if response.status_code == 200:
        with open(os.path.join(output_dir, f"{name}.svg"), "wb") as f:
            f.write(response.content)
        print(f"✅ Downloaded: {name}.svg")
    else:
        print(f"❌ Failed to download: {name} ({code})")

print("🎉 Download completed.")
