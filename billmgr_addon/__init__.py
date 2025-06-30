# -*- coding: utf-8 -*-

"""
BILLmanager Addon Framework

Универсальная Python-библиотека для создания плагинов BILLmanager.

Основные компоненты:
- Ядро плагина (core) - система маршрутизации и UI компоненты
- Работа с БД (db) - подключение к MySQL/MariaDB
- Авторизация (auth) - интеграция с сессиями BILLmanager
- CLI инструменты (cli) - команды для создания и установки плагинов
- Утилиты (utils) - вспомогательные функции
"""

# Ядро плагина
from .core import (
    create_app, 
    create_cgi_app, 
    create_cli_app,
    MgrAddonExtension,
    get_router
)

# Базовые классы эндпоинтов (ленивый импорт для избежания циклических зависимостей)
def _get_endpoint_classes():
    from .core.router import (
        MgrEndpoint, 
        ListEndpoint, 
        FormEndpoint, 
        ActionEndpoint,
        CgiEndpoint
    )
    return {
        'MgrEndpoint': MgrEndpoint,
        'ListEndpoint': ListEndpoint, 
        'FormEndpoint': FormEndpoint,
        'ActionEndpoint': ActionEndpoint,
        'CgiEndpoint': CgiEndpoint
    }

# Processing module классы (ленивый импорт)
def _get_processing_module_classes():
    from .core.processing import (
        ProcessingModule,
        ProcessingModuleCommand,
        FeaturesCommand,
        ServiceCommand,
        OpenCommand,
        ResumeCommand,
        SuspendCommand,
        CloseCommand,
        StartCommand,
        StopCommand,
        StatCommand,
        ProcessingModuleResponse,
        FeaturesResponse,
        create_processing_module_app
    )
    return {
        'ProcessingModule': ProcessingModule,
        'ProcessingModuleCommand': ProcessingModuleCommand,
        'FeaturesCommand': FeaturesCommand,
        'ServiceCommand': ServiceCommand,
        'OpenCommand': OpenCommand,
        'ResumeCommand': ResumeCommand,
        'SuspendCommand': SuspendCommand,
        'CloseCommand': CloseCommand,
        'StartCommand': StartCommand,
        'StopCommand': StopCommand,
        'StatCommand': StatCommand,
        'ProcessingModuleResponse': ProcessingModuleResponse,
        'FeaturesResponse': FeaturesResponse,
        'create_processing_module_app': create_processing_module_app
    }

# UI компоненты
def _get_ui_classes():
    from .core.ui import MgrForm, MgrList, MgrError
    return {
        'MgrForm': MgrForm,
        'MgrList': MgrList,
        'MgrError': MgrError
    }

# Типы запросов и ответов
def _get_request_response_classes():
    from .core.request_types import MgrRequest, CgiRequest
    from .core.response import MgrResponse, MgrErrorResponse, MgrSuccessResponse
    return {
        'MgrRequest': MgrRequest,
        'CgiRequest': CgiRequest, 
        'MgrResponse': MgrResponse,
        'MgrErrorResponse': MgrErrorResponse,
        'MgrSuccessResponse': MgrSuccessResponse
    }

# Работа с БД
from .db import get_db, DB, DBConfig, FlaskDbExtension

# Авторизация
from .auth import load_billmgr_user

# Утилиты
from .utils import (
    create_plugin_symlinks,
    XMLBuilder,
    setup_logger as get_logger,
    CustomJSONEncoder
)

# Готовые реализации основных файлов
from . import cgi, cli, build_xml

# WSGI интерфейс
from .wsgi import (
    create_wsgi_app,
    create_wsgi_app_from_endpoints,
    WSGIAdapter
)


# Ленивое создание модуля для удобного доступа к классам
class _LazyModule:
    def __init__(self):
        self._endpoint_classes = None
        self._ui_classes = None  
        self._request_response_classes = None
        self._processing_module_classes = None

    def __getattr__(self, name):
        # Пробуем найти в эндпоинтах
        if self._endpoint_classes is None:
            self._endpoint_classes = _get_endpoint_classes()
        if name in self._endpoint_classes:
            return self._endpoint_classes[name]
            
        # Пробуем найти в UI компонентах
        if self._ui_classes is None:
            self._ui_classes = _get_ui_classes()
        if name in self._ui_classes:
            return self._ui_classes[name]
            
        # Пробуем найти в запросах/ответах
        if self._request_response_classes is None:
            self._request_response_classes = _get_request_response_classes()
        if name in self._request_response_classes:
            return self._request_response_classes[name]
            
        # Пробуем найти в processing module
        if self._processing_module_classes is None:
            self._processing_module_classes = _get_processing_module_classes()
        if name in self._processing_module_classes:
            return self._processing_module_classes[name]
            
        raise AttributeError(f"module '{__name__}' has no attribute '{name}'")


import sys
_lazy = _LazyModule()

MgrEndpoint = property(lambda self: _lazy.MgrEndpoint)
ListEndpoint = property(lambda self: _lazy.ListEndpoint) 
FormEndpoint = property(lambda self: _lazy.FormEndpoint)
ActionEndpoint = property(lambda self: _lazy.ActionEndpoint)
CgiEndpoint = property(lambda self: _lazy.CgiEndpoint)
MgrForm = property(lambda self: _lazy.MgrForm)
MgrList = property(lambda self: _lazy.MgrList)
MgrError = property(lambda self: _lazy.MgrError)
MgrRequest = property(lambda self: _lazy.MgrRequest)
CgiRequest = property(lambda self: _lazy.CgiRequest)
MgrResponse = property(lambda self: _lazy.MgrResponse)
MgrErrorResponse = property(lambda self: _lazy.MgrErrorResponse)
MgrSuccessResponse = property(lambda self: _lazy.MgrSuccessResponse)
MgrOkResponse = property(lambda self: _lazy.MgrOkResponse)

# Processing Module классы
ProcessingModule = property(lambda self: _lazy.ProcessingModule)
ProcessingModuleCommand = property(lambda self: _lazy.ProcessingModuleCommand)
FeaturesCommand = property(lambda self: _lazy.FeaturesCommand)
ServiceCommand = property(lambda self: _lazy.ServiceCommand)
OpenCommand = property(lambda self: _lazy.OpenCommand)
ResumeCommand = property(lambda self: _lazy.ResumeCommand)
SuspendCommand = property(lambda self: _lazy.SuspendCommand)
CloseCommand = property(lambda self: _lazy.CloseCommand)
StartCommand = property(lambda self: _lazy.StartCommand)
StopCommand = property(lambda self: _lazy.StopCommand)
StatCommand = property(lambda self: _lazy.StatCommand)
ProcessingModuleResponse = property(lambda self: _lazy.ProcessingModuleResponse)
FeaturesResponse = property(lambda self: _lazy.FeaturesResponse)
create_processing_module_app = property(lambda self: _lazy.create_processing_module_app)

# Версия библиотеки
__version__ = '0.1.0'

# Экспорт основных компонентов
__all__ = [
    # Версия
    '__version__',
    
    # Ядро
    'create_app',
    'create_cgi_app', 
    'create_cli_app',
    'MgrAddonExtension',
    'get_router',
    
    # Эндпоинты
    'MgrEndpoint',
    'ListEndpoint',
    'FormEndpoint', 
    'ActionEndpoint',
    'CgiEndpoint',
    
    # Processing Module
    'ProcessingModule',
    'ProcessingModuleCommand',
    'FeaturesCommand',
    'ServiceCommand', 
    'OpenCommand',
    'ResumeCommand',
    'SuspendCommand',
    'CloseCommand',
    'StartCommand',
    'StopCommand',
    'StatCommand',
    'ProcessingModuleResponse',
    'FeaturesResponse',
    'create_processing_module_app',
    
    # UI компоненты
    'MgrForm',
    'MgrList',
    'MgrError',
    
    # Запросы и ответы
    'MgrRequest',
    'CgiRequest',
    'MgrResponse', 
    'MgrErrorResponse',
    'MgrSuccessResponse',
    'MgrOkResponse',
    
    # БД
    'get_db',
    'DB',
    'DBConfig',
    'FlaskDbExtension',
    
    # Авторизация
    'load_billmgr_user',
    
    # Утилиты
    'create_plugin_symlinks',
    'get_logger',
    'XMLBuilder',
    'CustomJSONEncoder',
    
    # WSGI
    'create_wsgi_app',
    'create_wsgi_app_from_endpoints',
    'WSGIAdapter'
]