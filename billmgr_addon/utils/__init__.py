# -*- coding: utf-8 -*-
"""
Утилиты для работы с плагинами
"""

from .billmgr_api import (
    AccountDiscountinfoRequest,
    BillmgrAPI,
    BillmgrApiError,
    BillmgrAPIResponse,
    BillmgrError,
    BillmgrRequestError,
    KeepAliveRequest,
    get_billmgr_api_as_config_user,
    get_billmgr_api_as_current_user,
)
from .files import config_path, create_plugin_symlinks, cwd_path, public_path, xml_path
from .serialization import CustomJSONEncoder, jsonify
from .xml_builder import XMLBuilder

__all__ = [
    # Пути
    "cwd_path",
    "config_path",
    "public_path",
    "xml_path",
    # Симлинки
    "create_plugin_symlinks",
    # XML
    "XMLBuilder",
    # Сериализация
    "CustomJSONEncoder",
    "jsonify",
    # API BILLmanager
    "BillmgrAPI",
    "BillmgrAPIResponse",
    "BillmgrError",
    "BillmgrRequestError",
    "BillmgrApiError",
    "KeepAliveRequest",
    "AccountDiscountinfoRequest",
    "get_billmgr_api_as_current_user",
    "get_billmgr_api_as_config_user",
]
