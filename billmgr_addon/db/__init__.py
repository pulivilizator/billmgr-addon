# -*- coding: utf-8 -*-
"""
Модуль для работы с бд
"""

from .db import DB, DBConfig, DBResult, FlaskDbExtension, get_db

__all__ = [
    "FlaskDbExtension",
    "DBConfig",
    "DB",
    "DBResult",
    "get_db",
]
