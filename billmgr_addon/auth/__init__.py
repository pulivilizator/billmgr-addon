# -*- coding: utf-8 -*-
"""
Модуль авторизации для BILLmanager
"""

from .auth import User, load_billmgr_user

__all__ = [
    "load_billmgr_user",
    "User",
]
