# pywebsearch.spec
# -*- mode: python -*-

from PyInstaller.utils.hooks import collect_submodules

block_cipher = None

project_dir = "."
source_subdir = "pywebsearch"

hidden_imports = collect_submodules('pybrowsers') + collect_submodules('PyQt6') + collect_submodules('platformdirs')

datas = [
    ("pywebsearch/icons/*.*", "icons"),
]


a = Analysis(
    [f"{project_dir}/{source_subdir}/main.py"],
    pathex=[f"{project_dir}/{source_subdir}"],
    binaries=[],
    datas=datas,
    hiddenimports=hidden_imports,
    hookspath=[],
    runtime_hooks=[],
    excludes=[],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name='pywebsearch',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=False,
    icon='pywebsearch/icons/pywebsearch.ico'
)

coll = COLLECT(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name='pywebsearch',
)
