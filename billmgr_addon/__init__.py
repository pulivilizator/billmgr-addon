# -*- coding: utf-8 -*-

"""
Основные компоненты:
- Ядро плагина (core) - система маршрутизации и UI компоненты
- Работа с БД (db) - подключение к MySQL/MariaDB
- Авторизация (auth) - интеграция с сессиями BILLmanager
- CLI инструменты (cli) - команды для создания и установки плагинов
- Утилиты (utils) - вспомогательные функции
"""

from .core import MgrAddonExtension, create_app, create_cgi_app, create_cli_app, get_router


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


from . import build_xml, cgi, cli
from .auth import load_billmgr_user
from .db import DB, DBConfig, FlaskDbExtension, get_db
from .utils import CustomJSONEncoder, XMLBuilder, create_plugin_symlinks, jsonify
from .utils.logging import LOGGER, LOGGER_NAME, setup_logger
from .wsgi import WSGIAdapter, create_wsgi_app, create_wsgi_app_from_endpoints


class _LazyModule:
    def __init__(self):
        self._endpoint_classes = None
        self._ui_classes = None
        self._request_response_classes = None

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


__version__ = "0.1.0"

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
    # Логгирование
    "setup_logger",
    "LOGGER",
    "LOGGER_NAME",
    # WSGI
    "create_wsgi_app",
    "create_wsgi_app_from_endpoints",
    "WSGIAdapter",
]
