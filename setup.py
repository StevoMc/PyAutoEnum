#!/usr/bin/env python3
"""
Setup script for PyAutoEnum.
"""

import os

from setuptools import find_packages, setup

# Get version from package __init__.py
with open(os.path.join("src", "pyautoenum", "__init__.py"), "r") as f:
    for line in f:
        if line.startswith("__version__"):
            version = line.split("=")[1].strip().strip('"').strip("'")
            break
    else:
        version = "0.2.0"

# Get long description from README.md
with open("README.md", "r") as f:
    long_description = f.read()

setup(
    name="pyautoenum",
    version=version,
    description="Automated Enumeration Tool for Security Testing",
    long_description=long_description,
    long_description_content_type="text/markdown",
    author="StevoMc",
    author_email="",  # Add your email or leave blank
    url="https://github.com/parzival-hub/PyAutoEnum",
    package_dir={"": "src"},
    packages=find_packages(where="src"),
    include_package_data=True,
    install_requires=[
        "beautifulsoup4>=4.9.0",
        "ping3>=4.0.0",
        "pysmb>=1.2.0",
        "python-nmap>=0.7.1",
        "PyYAML>=6.0.0",
        "requests>=2.25.0",
        "tqdm>=4.50.0",
    ],
    entry_points={
        "console_scripts": [
            "pyautoenum=pyautoenum.__main__:main",
        ],
    },
    classifiers=[
        "Development Status :: 3 - Alpha",
        "Intended Audience :: Information Technology",
        "Intended Audience :: System Administrators",
        "Topic :: Security",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "License :: OSI Approved :: MIT License",
        "Operating System :: POSIX :: Linux",
    ],
    python_requires=">=3.8",
)
