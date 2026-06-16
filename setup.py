#!/usr/bin/env python3
"""
Setup script for the FPGA Automation Tool (GUI-only).

Usage:
    pip install -e .          # development install
    pip install .             # regular install

After install you can run:
    run-fpga-gui            # or just "python -m run_fpga_gui"
"""

from setuptools import setup, find_packages

setup(
    name="logiclance-fpga",
    version="1.1.0",
    description="FPGA Automation Tool for Xilinx/AMD Vivado (GUI + advanced intelligence features)",
    long_description=open("README.md", encoding="utf-8").read(),
    long_description_content_type="text/markdown",
    author="Hemanth Kumar DM (enhanced by Grok)",
    url="https://github.com/hemanthkumardm/logiclance_fpga",
    license="LogicLance © 2026",

    packages=find_packages(include=["fpga_tool", "fpga_tool.*"]),

    install_requires=[
        "PyQt5>=5.15.0",
        "rich>=10.0.0",   # optional but recommended
    ],

    extras_require={
        "dev": [
            "pytest",
        ]
    },

    # Make the launcher scripts available after pip install
    scripts=[
        "run_fpga",
        "run_fpga_gui.py",
    ],

    # Alternative modern entry point (creates 'run-fpga-gui' command)
    entry_points={
        "console_scripts": [
            "run-fpga-gui=run_fpga_gui:main",
        ],
    },

    python_requires=">=3.8",

    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Science/Research",
        "Topic :: Scientific/Engineering :: Electronic Design Automation (EDA)",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "License :: Other/Proprietary License",
        "Operating System :: OS Independent",
    ],

    include_package_data=True,
)