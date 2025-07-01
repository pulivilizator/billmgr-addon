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
from .core import MgrAddonExtension, create_app, create_cgi_app, create_cli_app, get_router


# Базовые классы эндпоинтов (ленивый импорт для избежания циклических зависимостей)
def _get_endpoint_classes():
    from .core.router import ActionEndpoint, CgiEndpoint, FormEndpoint, ListEndpoint, MgrEndpoint

    return {
        "MgrEndpoint": MgrEndpoint,
        "ListEndpoint": ListEndpoint,
        "FormEndpoint": FormEndpoint,
        "ActionEndpoint": ActionEndpoint,
        "CgiEndpoint": CgiEndpoint,
    }


# Processing module классы (ленивый импорт)
def _get_processing_module_classes():
    from .core.processing import (
        OpenCommand,
        ProcessingModule,
        ProcessingModuleCommand,
        ProcessingModuleResponse,
        ServiceCommand,
    )

    return {
        "ProcessingModule": ProcessingModule,
        "ProcessingModuleCommand": ProcessingModuleCommand,
        "ServiceCommand": ServiceCommand,
        "OpenCommand": OpenCommand,
        "ProcessingModuleResponse": ProcessingModuleResponse,
    }


# UI компоненты
def _get_ui_classes():
    from .core.ui import MgrError, MgrForm, MgrList

    return {"MgrForm": MgrForm, "MgrList": MgrList, "MgrError": MgrError}


# Типы запросов и ответов
def _get_request_response_classes():
    from .core.request_types import CgiRequest, MgrRequest
    from .core.response import (
        MgrErrorResponse,
        MgrOkResponse,
        MgrRedirectResponse,
        MgrResponse,
        MgrSuccessResponse,
    )

    return {
        "MgrRequest": MgrRequest,
        "CgiRequest": CgiRequest,
        "MgrResponse": MgrResponse,
        "MgrErrorResponse": MgrErrorResponse,
        "MgrSuccessResponse": MgrSuccessResponse,
        "MgrOkResponse": MgrOkResponse,
        "MgrRedirectResponse": MgrRedirectResponse,
    }


# Работа с БД
# Готовые реализации основных файлов
from . import build_xml, cgi, cli

# Авторизация
from .auth import load_billmgr_user
from .db import DB, DBConfig, FlaskDbExtension, get_db

# Утилиты
from .utils import CustomJSONEncoder, XMLBuilder, create_plugin_symlinks, setup_logger as get_logger

# WSGI интерфейс
from .wsgi import WSGIAdapter, create_wsgi_app, create_wsgi_app_from_endpoints


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
MgrRedirectResponse = property(lambda self: _lazy.MgrRedirectResponse)

# Processing Module классы
ProcessingModule = property(lambda self: _lazy.ProcessingModule)
ProcessingModuleCommand = property(lambda self: _lazy.ProcessingModuleCommand)
ServiceCommand = property(lambda self: _lazy.ServiceCommand)
OpenCommand = property(lambda self: _lazy.OpenCommand)
ProcessingModuleResponse = property(lambda self: _lazy.ProcessingModuleResponse)


# Версия библиотеки
__version__ = "0.1.0"

# Экспорт основных компонентов
__all__ = [
    # Версия
    "__version__",
    # Ядро
    "create_app",
    "create_cgi_app",
    "create_cli_app",
    "MgrAddonExtension",
    "get_router",
    # Эндпоинты
    "MgrEndpoint",
    "ListEndpoint",
    "FormEndpoint",
    "ActionEndpoint",
    "CgiEndpoint",
    # Processing Module
    "ProcessingModule",
    "ProcessingModuleCommand",
    "ServiceCommand",
    "OpenCommand",
    "ProcessingModuleResponse",
    # UI компоненты
    "MgrForm",
    "MgrList",
    "MgrError",
    # Запросы и ответы
    "MgrRequest",
    "CgiRequest",
    "MgrResponse",
    "MgrErrorResponse",
    "MgrSuccessResponse",
    "MgrOkResponse",
    "MgrRedirectResponse",
    # БД
    "get_db",
    "DB",
    "DBConfig",
    "FlaskDbExtension",
    # Авторизация
    "load_billmgr_user",
    # Утилиты
    "create_plugin_symlinks",
    "get_logger",
    "XMLBuilder",
    "CustomJSONEncoder",
    # WSGI
    "create_wsgi_app",
    "create_wsgi_app_from_endpoints",
    "WSGIAdapter",
]
