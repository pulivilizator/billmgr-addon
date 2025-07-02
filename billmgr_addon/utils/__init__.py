# -*- coding: utf-8 -*-
"""
Утилиты для работы с BILLmanager
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
from .files import (
    config_path,
    create_plugin_symlinks,
    create_processing_module_symlinks,
    cwd_path,
    public_path,
    xml_path,
)
# Логгирование теперь экспортируется напрямую из основного модуля
from .serialization import CustomJSONEncoder
from .xml_builder import XMLBuilder

__all__ = [
    # Пути
    "cwd_path",
    "config_path",
    "public_path",
    "xml_path",
    # Симлинки
    "create_plugin_symlinks",
    "create_processing_module_symlinks",
    # XML
    "XMLBuilder",
    # Логирование экспортируется из основного модуля
    # Сериализация
    "CustomJSONEncoder",
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
