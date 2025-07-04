# -*- coding: utf-8 -*-

import sys
from importlib import import_module
from pathlib import Path
from typing import Callable, Iterable, Optional

import tomlkit
from flask import Flask

from .core import MgrAddonExtension, create_app as create_core_app


class WSGIAdapter:
    def __init__(
        self,
        plugin_name: Optional[str] = None,
        plugin_path: Optional[Path] = None,
        config_path: Optional[Path] = None,
    ):
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

        if str(self.plugin_path) not in sys.path:
            sys.path.insert(0, str(self.plugin_path))

    def _load_config(self, app: Flask) -> None:
        if self.config_path and self.config_path.exists():
            try:
                with open(self.config_path, "r") as f:
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
        app = create_core_app()

        self._load_config(app)

        if self.plugin_name:
            try:
                plugin_module = import_module(self.plugin_name)

                if hasattr(plugin_module, "endpoints"):
                    endpoints = plugin_module.endpoints
                elif hasattr(plugin_module, "ENDPOINTS"):
                    endpoints = plugin_module.ENDPOINTS
                else:
                    endpoints_module = import_module(f"{self.plugin_name}.endpoints")
                    endpoints = endpoints_module.endpoints

                mgr_addon = MgrAddonExtension()
                mgr_addon.init_app(app, endpoints)

            except ImportError as e:
                app.logger.error(f"Не удалось загрузить плагин {self.plugin_name}: {e}")
                raise

        return app

    def __call__(self, environ: dict, start_response: Callable) -> Iterable[bytes]:
        """
        Args:
            environ: WSGI environment
            start_response: WSGI start_response callback

        Returns:
            Response iterator
        """
        if not hasattr(self, "_app"):
            self._app = self.create_app()

        return self._app(environ, start_response)


def create_wsgi_app(
    plugin_name: Optional[str] = None,
    plugin_path: Optional[Path] = None,
    config_path: Optional[Path] = None,
) -> WSGIAdapter:
    """
    Args:
        plugin_name: Имя плагина
        plugin_path: Путь к плагину (по умолчанию текущая директория)
        config_path: Путь к конфигурации (по умолчанию не используется)

    Returns:
        WSGIAdapter: WSGI приложение
    """
    return WSGIAdapter(plugin_name=plugin_name, plugin_path=plugin_path, config_path=config_path)


def create_wsgi_app_from_endpoints(endpoints: list, config_path: Optional[Path] = None) -> Flask:
    app = create_core_app()

    if config_path and config_path.exists():
        try:
            with open(config_path, "r") as f:
                config = tomlkit.load(f)
                app.config.update(config)
        except Exception as e:
            app.logger.warning(f"Не удалось загрузить конфигурацию: {e}")

    mgr_addon = MgrAddonExtension()
    mgr_addon.init_app(app, endpoints)

    return app


def create_app(plugin_name: Optional[str] = None) -> Flask:
    adapter = WSGIAdapter(plugin_name=plugin_name)
    return adapter.create_app()
