#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from setuptools import find_packages, setup

setup(
    name="billmgr-addon",
    version="0.1.0",
    description="Universal framework for creating BILLmanager plugins",
    author="billmgr",
    packages=find_packages(),
    python_requires=">=3.8",
    install_requires=[
        "Flask[async]>=3.0.3",
        "Flask-Login>=0.6.3",
        "requests>=2.27.1",
        "httpx>=0.27.2",
        "tomlkit>=0.13.2",
        "pydantic>=2.9.2",
        "pycryptodome>=3.21.0",
        "fluent-compiler>=1.1",
        "ordered-set>=4.1.0",
        "watchdog>=4.0.2",
        "click>=8.1.7",
        "toml>=0.10.2",
        "cryptography==45.0.5",
    ],
    extras_require={
        "pymysql": [
            "PyMySQL>=1.1.0",
        ],
        "mysqlclient": [
            "mysqlclient>=2.2.4",
        ],
        "dev": [
            "mypy>=1.15.0",
            "ruff>=0.10.0",
        ],
        "celery": [
            "celery>=5.4.0",
        ],
        "websockets": [
            "websockets>=13.1",
        ],
        "full": [
            "celery>=5.4.0",
            "websockets>=13.1",
        ],
    },
    entry_points={
        "console_scripts": [
            "billmgr-addon=billmgr_addon.cli:main",
        ],
    },
    include_package_data=True,
    zip_safe=False,
)
