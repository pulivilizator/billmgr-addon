# -*- coding: utf-8 -*-

"""
Основные компоненты:
- Ядро плагина (core) - система маршрутизации и UI компоненты
- Работа с БД (db) - подключение к MySQL/MariaDB
- Авторизация (auth) - интеграция с сессиями BILLmanager
- CLI инструменты (cli) - команды для создания и установки плагинов
- Утилиты (utils) - вспомогательные функции
- Processing Module - модули обработки услуг
"""

from .core import MgrAddonExtension, create_app, create_cgi_app, create_cli_app, get_router
from .core.processing_module import create_processing_module_cli_app


def _get_endpoint_classes():
    from .core.router import ActionEndpoint, CgiEndpoint, FormEndpoint, ListEndpoint, MgrEndpoint

    return {
        "MgrEndpoint": MgrEndpoint,
        "ListEndpoint": ListEndpoint,
        "FormEndpoint": FormEndpoint,
        "ActionEndpoint": ActionEndpoint,
        "CgiEndpoint": CgiEndpoint,
    }


def _get_ui_classes():
    from .core.ui import MgrError, MgrForm, MgrList

    return {"MgrForm": MgrForm, "MgrList": MgrList, "MgrError": MgrError}


def _get_request_response_classes():
    from .core.request_types import CgiRequest, MgrRequest
    from .core.response import MgrErrorResponse, MgrOkResponse, MgrRedirectResponse, MgrResponse

    return {
        "MgrRequest": MgrRequest,
        "CgiRequest": CgiRequest,
        "MgrResponse": MgrResponse,
        "MgrErrorResponse": MgrErrorResponse,
        "MgrOkResponse": MgrOkResponse,
        "MgrRedirectResponse": MgrRedirectResponse,
    }


def _get_processing_module_classes():
    from .core.processing_module import (
        ProcessingModuleResponse,
        FeaturesResponse,
    )

    return {
        "ProcessingModuleResponse": ProcessingModuleResponse,
        "FeaturesResponse": FeaturesResponse,
    }


from . import build_xml, cgi, cli
from .auth import load_billmgr_user
from .db import DB, DBConfig, FlaskDbExtension, get_db
from .utils import CustomJSONEncoder, XMLBuilder, create_plugin_symlinks, jsonify
from .utils.logging import LOGGER, LOGGER_NAME, setup_logger
from .utils.mgrctl import mgrctl_exec


class _LazyModule:
    def __init__(self):
        self._endpoint_classes = None
        self._ui_classes = None
        self._request_response_classes = None
        self._processing_module_classes = None

    def __getattr__(self, name):
        if self._endpoint_classes is None:
            self._endpoint_classes = _get_endpoint_classes()
        if name in self._endpoint_classes:
            return self._endpoint_classes[name]

        if self._ui_classes is None:
            self._ui_classes = _get_ui_classes()
        if name in self._ui_classes:
            return self._ui_classes[name]

        if self._request_response_classes is None:
            self._request_response_classes = _get_request_response_classes()
        if name in self._request_response_classes:
            return self._request_response_classes[name]

        if self._processing_module_classes is None:
            self._processing_module_classes = _get_processing_module_classes()
        if name in self._processing_module_classes:
            return self._processing_module_classes[name]

        raise AttributeError(f"module '{__name__}' has no attribute '{name}'")


import sys

_lazy = _LazyModule()

MgrEndpoint = _lazy.MgrEndpoint
ListEndpoint = _lazy.ListEndpoint
FormEndpoint = _lazy.FormEndpoint
ActionEndpoint = _lazy.ActionEndpoint
CgiEndpoint = _lazy.CgiEndpoint
MgrForm = _lazy.MgrForm
MgrList = _lazy.MgrList
MgrError = _lazy.MgrError
MgrRequest = _lazy.MgrRequest
CgiRequest = _lazy.CgiRequest
MgrResponse = _lazy.MgrResponse
MgrErrorResponse = _lazy.MgrErrorResponse
MgrOkResponse = _lazy.MgrOkResponse
MgrRedirectResponse = _lazy.MgrRedirectResponse

# Processing Module classes
ProcessingModuleResponse = _lazy.ProcessingModuleResponse
FeaturesResponse = _lazy.FeaturesResponse


__all__ = [
    # Ядро
    "create_app",
    "create_cgi_app",
    "create_cli_app",
    "create_processing_module_cli_app",
    "MgrAddonExtension",
    "get_router",
    # Эндпоинты
    "MgrEndpoint",
    "ListEndpoint",
    "FormEndpoint",
    "ActionEndpoint",
    "CgiEndpoint",
    # UI компоненты
    "MgrForm",
    "MgrList",
    "MgrError",
    # Запросы и ответы
    "MgrRequest",
    "CgiRequest",
    "MgrResponse",
    "MgrErrorResponse",
    "MgrOkResponse",
    "MgrRedirectResponse",
    # Processing Module
    "ProcessingModuleResponse",
    "FeaturesResponse",
    # БД
    "get_db",
    "DB",
    "DBConfig",
    "FlaskDbExtension",
    # Авторизация
    "load_billmgr_user",
    # Утилиты
    "create_plugin_symlinks",
    "XMLBuilder",
    "CustomJSONEncoder",
    "jsonify",
    "mgrctl_exec",
    # Логгирование
    "setup_logger",
    "LOGGER",
    "LOGGER_NAME",
]
