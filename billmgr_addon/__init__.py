# -*- coding: utf-8 -*-
"""
BILLmanager Addon Framework
==========================

Универсальная библиотека для создания плагинов BILLmanager.

Основные компоненты:
- Ядро плагина (core)
- Работа с БД (db)
- Авторизация (auth)
- CLI интерфейсы (cli)
- Утилиты (utils)
- Шаблоны проектов (scaffold)
"""

__version__ = '0.1.0'
__author__ = 'BILLmanager Team'

# Основные импорты для удобства использования
from .core import (
    create_app, create_cgi_app, create_cli_app,
    MgrEndpoint, ListEndpoint, FormEndpoint, ActionEndpoint,
    CgiEndpoint, DownloadCgiEndpoint, HtmlCgiEndpoint,
    MgrRouter, MgrForm, MgrList, MgrError, MgrRequest
)
from .db import FlaskDbExtension, DBConfig, get_db
from .auth import load_billmgr_user, User  
from .utils import cwd_path, config_path, create_plugin_symlinks

__all__ = [
    # App factories
    'create_app',
    'create_cgi_app', 
    'create_cli_app',
    
    # Endpoints
    'MgrEndpoint',
    'ListEndpoint',
    'FormEndpoint', 
    'ActionEndpoint',
    'CgiEndpoint',
    'DownloadCgiEndpoint',
    'HtmlCgiEndpoint',
    
    # Core components
    'MgrRouter',
    'MgrForm',
    'MgrList',
    'MgrError',
    
    # Database
    'FlaskDbExtension',
    'DBConfig',
    'get_db',
    
    # Auth
    'load_billmgr_user',
    'User',
    
    # Utils
    'cwd_path',
    'config_path',
    'create_plugin_symlinks',
] 