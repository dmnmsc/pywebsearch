from setuptools import setup, find_packages

setup(
    name="pywebsearch",
    version="3.6.0",
    description="Customizable web search tool with aliases, !bangs, and GUI",
    author="dmnmsc",
    url="https://github.com/dmnmsc/pywebsearch",
    license="GPL-3.0",
    packages=find_packages(),

    install_requires=[
        "pybrowsers",
        "PyQt6",
        "platformdirs"
    ],
    extras_require={
        "windows": ["installed-browsers"],
    },
    entry_points={
        "console_scripts": [
            "pywebsearch = pywebsearch.main:main"
        ]
    },
    include_package_data=True,
    package_data={
        "pywebsearch": ["icons/*.*"],
    },
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: GNU General Public License v3 (GPLv3)",
        "Operating System :: OS Independent",
    ],
    python_requires=">=3.7",
)