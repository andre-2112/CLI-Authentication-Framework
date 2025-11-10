#!/usr/bin/env python3
"""
Setup script for CCA SDK and CLI
"""

from setuptools import setup, find_packages
from pathlib import Path

# Read the README
readme_file = Path(__file__).parent / "README.md"
long_description = ""
if readme_file.exists():
    with open(readme_file, 'r', encoding='utf-8') as f:
        long_description = f.read()

# Read requirements
requirements_file = Path(__file__).parent / "requirements.txt"
if requirements_file.exists():
    with open(requirements_file) as f:
        requirements = [line.strip() for line in f if line.strip() and not line.startswith('#')]
else:
    requirements = ['boto3>=1.26.0']

setup(
    name="cca-sdk",
    version="0.3.0",
    author="2112 Lab",
    author_email="info@2112-lab.com",
    description="CLI Authentication Framework - Secure AWS authentication using Amazon Cognito",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/andre-2112/CLI-Authentication-Framework",
    packages=find_packages(exclude=['tests', 'docs']),
    py_modules=["ccc"],
    classifiers=[
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
        "Development Status :: 4 - Beta",
        "Intended Audience :: Developers",
        "Intended Audience :: System Administrators",
        "Topic :: Software Development :: Libraries :: Python Modules",
        "Topic :: System :: Systems Administration",
    ],
    python_requires=">=3.8",
    install_requires=requirements,
    entry_points={
        "console_scripts": [
            "ccc=ccc:main",
        ],
    },
    keywords='aws cognito authentication cli sdk',
    project_urls={
        'Documentation': 'https://github.com/andre-2112/CLI-Authentication-Framework/tree/master/docs',
        'Source': 'https://github.com/andre-2112/CLI-Authentication-Framework',
        'Tracker': 'https://github.com/andre-2112/CLI-Authentication-Framework/issues',
    },
)
