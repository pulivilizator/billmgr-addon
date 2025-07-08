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
from ..utils.logging import setup_logger

logger = setup_logger(__name__)


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


class ProcessingModuleHandler(ABC):
    """
    Базовый обработчик команд processing module
    
    Наследники должны реализовать методы для обработки команд lifecycle услуг.
    """
    
    @abstractmethod
    def get_itemtypes(self) -> List[Dict[str, str]]:
        """
        Вернуть список типов услуг которые обрабатывает модуль
        
        Returns:
            Список словарей с описанием типов услуг
            
        Examples:
            [{"name": "myservice"}]
        """
        pass
    
    @abstractmethod
    def get_features(self) -> List[Dict[str, str]]:
        """
        Вернуть список поддерживаемых команд
        
        Returns:
            Список словарей с описанием команд
            
        Examples:
            [
                {"name": "features"},
                {"name": "open"},
                {"name": "suspend"},
                {"name": "resume"},
                {"name": "close"},
                {"name": "stat"}
            ]
        """
        pass
    
    @abstractmethod
    def get_params(self) -> List[Dict[str, str]]:
        """
        Вернуть список параметров конфигурации
        
        Returns:
            Список словарей с описанием параметров
            
        Examples:
            [
                {"name": "api_url"},
                {"name": "api_token", "crypted": "yes"}
            ]
        """
        pass
    
    def features_command(self, **kwargs) -> FeaturesResponse:
        """Обработка команды features"""
        return FeaturesResponse(
            itemtypes=self.get_itemtypes(),
            features=self.get_features(),
            params=self.get_params()
        )
    
    def open_command(self, item_id: Optional[int] = None, runningoperation: Optional[str] = None, **kwargs) -> ProcessingModuleResponse:
        """
        Обработка команды open - активация услуги
        
        Args:
            item_id: ID услуги
            runningoperation: ID операции
            **kwargs: Дополнительные параметры
            
        Returns:
            Ответ команды
        """
        logger.info(f"Processing open command for item {item_id}")
        return ProcessingModuleResponse("ok")
    
    def resume_command(self, item_id: Optional[int] = None, runningoperation: Optional[str] = None, **kwargs) -> ProcessingModuleResponse:
        """
        Обработка команды resume - возобновление услуги
        """
        logger.info(f"Processing resume command for item {item_id}")
        return ProcessingModuleResponse("ok")
    
    def suspend_command(self, item_id: Optional[int] = None, runningoperation: Optional[str] = None, **kwargs) -> ProcessingModuleResponse:
        """
        Обработка команды suspend - приостановка услуги
        """
        logger.info(f"Processing suspend command for item {item_id}")
        return ProcessingModuleResponse("ok")
    
    def close_command(self, item_id: Optional[int] = None, runningoperation: Optional[str] = None, **kwargs) -> ProcessingModuleResponse:
        """
        Обработка команды close - закрытие услуги
        """
        logger.info(f"Processing close command for item {item_id}")
        return ProcessingModuleResponse("ok")
    
    def start_command(self, item_id: Optional[int] = None, runningoperation: Optional[str] = None, **kwargs) -> ProcessingModuleResponse:
        """
        Обработка команды start - запуск услуги
        """
        logger.info(f"Processing start command for item {item_id}")
        return ProcessingModuleResponse("ok")
    
    def stop_command(self, item_id: Optional[int] = None, runningoperation: Optional[str] = None, **kwargs) -> ProcessingModuleResponse:
        """
        Обработка команды stop - остановка услуги
        """
        logger.info(f"Processing stop command for item {item_id}")
        return ProcessingModuleResponse("ok")
    
    def stat_command(self, module_id: Optional[int] = None, **kwargs) -> ProcessingModuleResponse:
        """
        Обработка команды stat - сбор статистики
        """
        logger.info(f"Processing stat command for module {module_id}")
        return ProcessingModuleResponse("ok")


def create_processing_module_blueprint(handler: ProcessingModuleHandler, blueprint_name: str = "processing_module") -> Blueprint:
    """
    Создать Blueprint для processing module
    
    Args:
        handler: Обработчик команд processing module
        blueprint_name: Имя blueprint
        
    Returns:
        Настроенный Blueprint
    """
    bp = Blueprint(blueprint_name, __name__)

    @bp.cli.command("execute")
    @click.option("--command", type=str, required=True)
    @click.option("--subcommand", type=str)
    @click.option("--id", "pricelist_id", type=int)
    @click.option("--item", "item_id", type=int)
    @click.option("--module", "module_id", type=int)
    @click.option("--param", type=str)
    @click.option("--value")
    @click.option("--runningoperation")
    @click.option("--level")
    @click.option("--userid", "user_id")
    def execute(
        command,
        subcommand,
        pricelist_id,
        item_id,
        module_id,
        param,
        value,
        runningoperation,
        level,
        user_id,
    ):
        """Выполнить команду processing module"""
        commands = {
            "features": handler.features_command,
            "open": handler.open_command,
            "resume": handler.resume_command,
            "suspend": handler.suspend_command,
            "close": handler.close_command,
            "start": handler.start_command,
            "stop": handler.stop_command,
            "stat": handler.stat_command,
        }
        
        command_handler = commands.get(command)
        if command_handler is None:
            raise click.UsageError(f"Option --command has invalid value '{command}'")

        ctx = click.get_current_context()
        try:
            response = command_handler(**ctx.params)
            click.echo(response)
        except Exception as e:
            logger.exception(e)
            click.echo(MgrErrorResponse("Unknown processing module error"))

    return bp


def get_service_status(item_id: int, db_alias: str = "billmgr") -> Optional[Dict[str, Any]]:
    """
    Получить статус услуги из БД
    
    Args:
        item_id: ID услуги
        db_alias: Алиас подключения к БД
        
    Returns:
        Словарь с данными услуги или None
    """
    db = get_db(db_alias)
    return db.select_query(
        """
        SELECT i.*, i.status as service_status
        FROM item i
        WHERE i.id = %(item_id)s
        """, 
        {"item_id": item_id}
    ).one_or_none()


def set_service_status_active(item_id: int):
    """
    Установить статус услуги как активная через mgrctl
    
    Args:
        item_id: ID услуги
    """
    cmd = ["service.postopen", f"elid={item_id}", "sok=ok"]
    mgrctl_exec(cmd)


def set_service_status_suspended(item_id: int):
    """
    Установить статус услуги как приостановленная через mgrctl
    
    Args:
        item_id: ID услуги
    """
    cmd = ["service.postsuspend", f"elid={item_id}", "sok=ok"]
    mgrctl_exec(cmd)


def set_service_status_resumed(item_id: int):
    """
    Установить статус услуги как возобновленная через mgrctl
    
    Args:
        item_id: ID услуги
    """
    cmd = ["service.postresume", f"elid={item_id}", "sok=ok"]
    mgrctl_exec(cmd)


def set_service_status_closed(item_id: int):
    """
    Установить статус услуги как закрытая через mgrctl
    
    Args:
        item_id: ID услуги
    """
    cmd = ["service.postclose", f"elid={item_id}", "sok=ok"]
    mgrctl_exec(cmd) 