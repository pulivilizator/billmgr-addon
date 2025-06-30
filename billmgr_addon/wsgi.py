# -*- coding: utf-8 -*-
"""
WSGI интерфейс для BILLmanager плагинов

Этот модуль предоставляет WSGI адаптер для запуска плагинов
через WSGI-совместимые серверы (Gunicorn, uWSGI, mod_wsgi и др.)
"""

import os
import sys
from pathlib import Path
from typing import Callable, Optional, Iterable
from importlib import import_module

from flask import Flask
import tomlkit

from .core import create_app as create_core_app, MgrAddonExtension


class WSGIAdapter:
    """
    Адаптер для запуска BILLmanager плагинов через WSGI
    
    Поддерживает динамическую загрузку плагина и его эндпоинтов.
    """
    
    def __init__(self, plugin_name: Optional[str] = None, 
                 plugin_path: Optional[Path] = None,
                 config_path: Optional[Path] = None):
        """
        Инициализация WSGI адаптера
        
        Args:
            plugin_name: Имя плагина для импорта
            plugin_path: Путь к директории плагина
            config_path: Путь к файлу конфигурации
        """
        self.plugin_name = plugin_name
        self.plugin_path = plugin_path or Path.cwd()
        self.config_path = config_path
        
        # Добавляем путь плагина в sys.path
        if str(self.plugin_path) not in sys.path:
            sys.path.insert(0, str(self.plugin_path))
    
    def _load_config(self, app: Flask) -> None:
        """Загрузить конфигурацию из файла"""
        if self.config_path and self.config_path.exists():
            try:
                with open(self.config_path, 'r') as f:
                    config = tomlkit.load(f)
                    app.config.update(config)
            except Exception as e:
                app.logger.warning(f"Не удалось загрузить конфигурацию: {e}")

    def create_app(self) -> Flask:
        """
        Создать Flask приложение для WSGI
        
        Returns:
            Flask: Настроенное приложение
        """
        # Создаем базовое приложение
        app = create_core_app()
        
        # Загружаем конфигурацию
        self._load_config(app)
        
        # Загружаем эндпоинты плагина
        if self.plugin_name:
            try:
                # Импортируем модуль плагина
                plugin_module = import_module(self.plugin_name)
                
                # Ищем список эндпоинтов
                if hasattr(plugin_module, 'endpoints'):
                    endpoints = plugin_module.endpoints
                elif hasattr(plugin_module, 'ENDPOINTS'):
                    endpoints = plugin_module.ENDPOINTS
                else:
                    # Пытаемся найти в подмодуле endpoints
                    endpoints_module = import_module(f"{self.plugin_name}.endpoints")
                    endpoints = endpoints_module.endpoints
                
                # Регистрируем эндпоинты
                mgr_addon = MgrAddonExtension()
                mgr_addon.init_app(app, endpoints)
                    
            except ImportError as e:
                app.logger.error(f"Не удалось загрузить плагин {self.plugin_name}: {e}")
                raise
        
        return app
    
    def __call__(self, environ: dict, start_response: Callable) -> Iterable[bytes]:
        """
        WSGI вызов - делегируем Flask приложению
        
        Args:
            environ: WSGI environment
            start_response: WSGI start_response callback
            
        Returns:
            Response iterator
        """
        if not hasattr(self, '_app'):
            self._app = self.create_app()
        
        return self._app(environ, start_response)


def create_wsgi_app(plugin_name: Optional[str] = None,
                   plugin_path: Optional[Path] = None,
                   config_path: Optional[Path] = None) -> WSGIAdapter:
    """
    Фабрика для создания WSGI приложения
    
    Args:
        plugin_name: Имя плагина
        plugin_path: Путь к плагину
        config_path: Путь к конфигурации
        
    Returns:
        WSGIAdapter: WSGI приложение
    """
    return WSGIAdapter(
        plugin_name=plugin_name,
        plugin_path=plugin_path,
        config_path=config_path
    )


def create_wsgi_app_from_endpoints(endpoints: list,
                                  config_path: Optional[Path] = None) -> Flask:
    """
    Создать WSGI приложение напрямую из списка эндпоинтов
    
    Args:
        endpoints: Список эндпоинтов
        config_path: Путь к конфигурации
        
    Returns:
        Flask: Готовое WSGI приложение
    """
    app = create_core_app()
    
    # Загружаем конфигурацию если указана
    if config_path and config_path.exists():
        try:
            with open(config_path, 'r') as f:
                config = tomlkit.load(f)
                app.config.update(config)
        except Exception as e:
            app.logger.warning(f"Не удалось загрузить конфигурацию: {e}")
    
    # Регистрируем эндпоинты
    mgr_addon = MgrAddonExtension()
    mgr_addon.init_app(app, endpoints)
    
    return app


# Для обратной совместимости
def create_app(plugin_name: Optional[str] = None) -> Flask:
    """
    Создать Flask приложение для указанного плагина
    
    Args:
        plugin_name: Имя плагина
        
    Returns:
        Flask: Приложение
    """
    adapter = WSGIAdapter(plugin_name=plugin_name)
    return adapter.create_app() 