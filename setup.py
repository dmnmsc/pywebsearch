from setuptools import setup, find_packages

setup(
    name="pywebsearch",
    version="3.6.0",
    description="Customizable web search tool with aliases, !bangs, and GUI",
    author="dmnmsc",
    url="https://github.com/dmnmsc/pywebsearch",
    license="GPL-3.0",
    packages=find_packages(),
    py_modules=[
        "main", "app_settings", "search", "alias", "dialogs", "history", "backup", "config", "platform_base", "windows", "linux"
    ],
    install_requires=[
        "pybrowsers",       # Dependencia universal
        "PyQt6",
        "platformdirs"
    ],
    extras_require={
        "windows": ["installed-browsers"],   # Solo para Windows
    },
    entry_points={
        "console_scripts": [
            "pywebsearch = main:main"
        ]
    },
    include_package_data=True,
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: GNU General Public License v3 (GPLv3)",
        "Operating System :: OS Independent",
    ],
    python_requires=">=3.7",
)
