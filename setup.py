"""
Setup script for the Forex Factory Sentiment Analyzer.
"""
from setuptools import setup, find_packages

with open("README.md", "r") as fh:
    long_description = fh.read()

with open("requirements.txt", "r") as fh:
    requirements = fh.read().splitlines()

setup(
    name="forex-factory-sentiment",
    version="0.1.0",
    author="Your Name",
    author_email="your.email@example.com",
    description="A tool to analyze economic indicators from Forex Factory calendar to determine currency sentiment",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/yourusername/forex-factory-sentiment",
    packages=find_packages(),
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    python_requires=">=3.7",
    install_requires=requirements,
    entry_points={
        "console_scripts": [
            "forex-sentiment=src.main:main",
        ],
    },
) 