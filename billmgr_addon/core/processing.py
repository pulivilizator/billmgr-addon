# -*- coding: utf-8 -*-

"""
Модуль обработки услуг (Processing Module) для BILLmanager
"""

import click
from abc import ABC, abstractmethod
from typing import Optional, Dict, Any, List
from flask import Blueprint
import xml.etree.ElementTree as ET

from .response import MgrResponse, MgrOkResponse, MgrErrorResponse


class ProcessingModuleResponse(MgrResponse):
    """Базовый ответ processing module"""
    
    def __init__(self, content: str = ""):
        super().__init__(content)


class ProcessingModuleCommand(ABC):
    """Базовый класс для команд processing module"""
    
    @abstractmethod
    async def execute(self, **kwargs) -> ProcessingModuleResponse:
        """Выполнить команду"""
        raise NotImplementedError


class ServiceCommand(ProcessingModuleCommand):
    """Базовый класс для команд работы с услугами"""
    
    @abstractmethod
    async def execute(self, item_id: int = None, runningoperation: str = None, **kwargs) -> ProcessingModuleResponse:
        """Выполнить команду для услуги"""
        raise NotImplementedError


class OpenCommand(ServiceCommand):
    """Команда открытия (создания) услуги"""
    
    @abstractmethod
    async def execute(self, item_id: int = None, runningoperation: str = None, **kwargs) -> ProcessingModuleResponse:
        """Открыть (создать) услугу"""
        raise NotImplementedError


class ProcessingModule:
    """Основной класс processing module"""
    
    def __init__(self, module_name: str):
        self.module_name = module_name
        self.commands: Dict[str, ProcessingModuleCommand] = {}
    
    def register_command(self, command_name: str, command: ProcessingModuleCommand):
        """Зарегистрировать команду"""
        self.commands[command_name] = command
    
    def register_open(self, command: OpenCommand):
        """Зарегистрировать команду открытия услуги"""
        self.register_command("open", command)


# Экспорт классов
__all__ = [
    'ProcessingModuleResponse',
    'ProcessingModuleCommand',
    'ServiceCommand',
    'OpenCommand',
    'ProcessingModule'
]
