# -*- coding: utf-8 -*-

"""
Processing Module для плагинов
"""

import xml.etree.ElementTree as ET
from abc import ABC, abstractmethod
from typing import Dict, List, Optional, Any
import click
from flask import Blueprint, current_app

from ..core.response import MgrResponse, MgrErrorResponse
from ..db import get_db
from ..utils.mgrctl import mgrctl_exec
from ..utils.logging import LOGGER


class ProcessingModuleResponse(MgrResponse):
    """Базовый ответ processing module"""
    
    def __init__(self, content: str = ""):
        super().__init__()
        if content:
            self.root.text = content


class FeaturesResponse(MgrResponse):
    """Ответ команды features - описывает возможности модуля"""
    
    def __init__(
        self, 
        itemtypes: List[Dict[str, str]], 
        features: List[Dict[str, str]], 
        params: List[Dict[str, str]]
    ):
        super().__init__()
        
        itemtypes_element = ET.SubElement(self.root, "itemtypes")
        for itemtype_attributes in itemtypes:
            ET.SubElement(itemtypes_element, "itemtype", attrib=itemtype_attributes)

        features_element = ET.SubElement(self.root, "features")
        for feature_attributes in features:
            ET.SubElement(features_element, "feature", attrib=feature_attributes)

        params_element = ET.SubElement(self.root, "params")
        for param_attributes in params:
            ET.SubElement(params_element, "param", attrib=param_attributes)


def create_processing_module_cli_app(processing_module_bp, cli_group=None):
    """
    Создать CLI приложение для processing module
    
    Автоматически импортирует handler из приложения и создает CLI
    
    Returns:
        Flask: Настроенное CLI приложение
    """
    from . import create_common_app
    
    app = create_common_app()
        
    app.register_blueprint(processing_module_bp, cli_group=None)
    LOGGER.info("Processing module CLI app created with custom handler")
    
    return app


__all__ = [
    "ProcessingModuleResponse", 
    "FeaturesResponse",
    "create_processing_module_cli_app",
] 