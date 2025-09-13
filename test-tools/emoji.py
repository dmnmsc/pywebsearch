import os
import requests

# Diccionario con nombre y código Unicode del emoji
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

# Carpeta de salida
output_dir = "twemoji_svgs"
os.makedirs(output_dir, exist_ok=True)

# URL base del repositorio Twemoji
base_url = "https://raw.githubusercontent.com/jdecked/twemoji/master/assets/svg"

for name, code in emojis.items():
    url = f"{base_url}/{code}.svg"
    response = requests.get(url)
    if response.status_code == 200:
        with open(os.path.join(output_dir, f"{name}.svg"), "wb") as f:
            f.write(response.content)
        print(f"✅ Descargado: {name}.svg")
    else:
        print(f"❌ No se pudo descargar: {name} ({code})")

print("🎉 Descarga completada.")
