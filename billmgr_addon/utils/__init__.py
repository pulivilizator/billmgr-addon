# -*- coding: utf-8 -*-
"""
Утилиты для работы с BILLmanager
"""

from .files import (
    cwd_path,
    config_path,
    public_path,
    xml_path,
    create_plugin_symlinks,
    create_processing_module_symlinks,
)
from .xml_builder import XMLBuilder
from .logging import setup_logger
from .serialization import CustomJSONEncoder

__all__ = [
    # Пути
    'cwd_path',
    'config_path', 
    'public_path',
    'xml_path',
    
    # Симлинки
    'create_plugin_symlinks',
    'create_processing_module_symlinks',
    
    # XML
    'XMLBuilder',
    
    # Логирование
    'setup_logger',
    
    # Сериализация
    'CustomJSONEncoder',
] 