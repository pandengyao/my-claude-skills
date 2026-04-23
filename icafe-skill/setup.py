from setuptools import setup, find_packages

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

setup(
    name="icafe-skill",
    version="0.4.3",
    author="iCafe Team",
    author_email="icafe@baidu.com",
    description="A Python SDK for iCafe card operations",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/baidu/icafe-skill",
    packages=find_packages(),
    classifiers=[
        "Development Status :: 3 - Alpha",
        "Intended Audience :: Developers",
        "Topic :: Software Development :: Libraries :: Python Modules",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
    ],
    python_requires=">=3.8",
    install_requires=[
        "requests>=2.31.0",
        "pyyaml>=6.0",
        "click>=8.1.0",
    ],
)