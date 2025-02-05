"""
Setup file for Village Life.
"""

from setuptools import setup, find_packages

setup(
    name="village_life",
    version="0.1.0",
    packages=find_packages(),
    install_requires=[
        "PyQt6>=6.8.0",
        "pytest>=8.3.4",
        "pytest-qt>=4.2.0",
        "pytest-asyncio>=0.23.3",
        "pytest-timeout>=2.3.1",
        "pytest-benchmark>=5.1.0",
        "pytest-cov>=6.0.0",
        "pytest-xdist>=3.6.1",
    ],
    python_requires=">=3.12",
    author="Your Name",
    author_email="your.email@example.com",
    description="A text-based village life simulation game",
    long_description=open("README.md").read(),
    long_description_content_type="text/markdown",
    url="https://github.com/yourusername/village-life",
    classifiers=[
        "Development Status :: 3 - Alpha",
        "Intended Audience :: End Users/Desktop",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3.12",
        "Topic :: Games/Entertainment :: Simulation",
    ],
) 