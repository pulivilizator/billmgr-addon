#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from setuptools import setup, find_packages
import os

# Читаем README для long_description
readme_path = os.path.join(os.path.dirname(__file__), 'README.md')
long_description = ''
if os.path.exists(readme_path):
    with open(readme_path, 'r', encoding='utf-8') as f:
        long_description = f.read()

setup(
    name='billmgr-addon',
    version='0.1.0',
    description='Universal framework for creating BILLmanager plugins',
    long_description=long_description,
    long_description_content_type='text/markdown',
    author='BILLmanager Team',
    author_email='support@billmanager.com',
    url='https://github.com/billmanager/billmgr-addon',
    packages=find_packages(),
    python_requires='>=3.8',
    install_requires=[
        'Flask[async]>=3.0.0',
        'Flask-Login>=0.6.0',
        'mysqlclient>=2.2.0',
        'requests>=2.27.0',
        'httpx>=0.27.0',
        'tomlkit>=0.13.0',
        'pydantic>=2.9.0',
        'pycryptodome>=3.21.0',
        'fluent-compiler>=1.1',
        'ordered-set>=4.1.0',
        'watchdog>=4.0.0',
        'click>=8.0.0',
    ],
    extras_require={
        'dev': [
            'mypy>=1.0.0',
            'ruff>=0.1.0',
            'pytest>=7.0.0',
            'pytest-asyncio>=0.21.0',
        ],
        'celery': [
            'celery>=5.4.0',
        ],
        'websockets': [
            'websockets>=13.1',
        ],
    },
    entry_points={
        'console_scripts': [
            'billmgr-addon=billmgr_addon.cli:main',
        ],
    },
    include_package_data=True,
    package_data={
        'billmgr_addon': [
            'templates/**/*',
            'static/**/*',
            'xml_templates/**/*',
        ],
    },
    classifiers=[
        'Development Status :: 3 - Alpha',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: MIT License',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.8',
        'Programming Language :: Python :: 3.9',
        'Programming Language :: Python :: 3.10',
        'Programming Language :: Python :: 3.11',
        'Programming Language :: Python :: 3.12',
        'Framework :: Flask',
        'Topic :: Internet :: WWW/HTTP :: Dynamic Content',
        'Topic :: Software Development :: Libraries :: Python Modules',
    ],
    keywords='billmanager plugin framework web billing',
    zip_safe=False,
) 