# -*- coding: utf-8 -*-

"""
Ядро плагина BILLmanager

Предоставляет основные компоненты для создания плагинов:
- Система маршрутизации (MgrRouter)
- UI компоненты (MgrForm, MgrList, MgrError)
- Типы запросов и ответов
- Базовые классы эндпоинтов
"""

import logging
from types import SimpleNamespace

from flask import Flask, appcontext_pushed, g


def get_router():
    """Получить экземпляр роутера из контекста Flask"""
    extension_namespace = getattr(g, MgrAddonExtension.namespace_id)
    return extension_namespace.router


class MgrAddonExtension:
    """
    Расширение Flask для работы с BILLmanager плагинами

    Предоставляет систему маршрутизации, UI компоненты и интеграцию с BILLmanager.
    """

    namespace_id = "_mgr_addon"

    def __init__(self):
        self.router = None

    def init_app(self, app: Flask, endpoints):
        """
        Инициализировать расширение с Flask приложением

        Args:
            app: Flask приложение
            endpoints: Список эндпоинтов плагина
        """
        # Ленивый импорт для избежания циклических зависимостей
        from .router import MgrRouter

        self.router = MgrRouter(app, endpoints)

        appcontext_pushed.connect(self.appcontext_pushed_handler, app)
        app.teardown_appcontext(self.teardown_appcontext_handler)

        logging.debug(
            f'MgrAddonExtension extension initialized with "{MgrAddonExtension.namespace_id}" namespace'
        )

    def appcontext_pushed_handler(self, sender):
        """Обработчик создания контекста приложения"""
        try:
            extension_namespace = SimpleNamespace()
            extension_namespace.router = self.router
            setattr(g, MgrAddonExtension.namespace_id, extension_namespace)
        except Exception as e:
            logging.exception(e)

    def teardown_appcontext_handler(self, error):
        """Обработчик завершения контекста приложения"""
        extension_namespace = getattr(g, MgrAddonExtension.namespace_id)
        # Здесь можно добавить очистку ресурсов

    def on_extension_close(self):
        """Обработчик закрытия расширения"""
        logging.debug(
            f'MgrAddonExtension extension with "{MgrAddonExtension.namespace_id}" namespace is closed'
        )


def create_app():
    """
    Создать базовое Flask приложение для плагина

    Returns:
        Flask: Настроенное приложение
    """
    app = Flask(__name__)

    # Базовая конфигурация
    app.config.update(
        {
            "DEBUG": False,
            "SECRET_KEY": "change-me-in-production",
        }
    )

    return app


def create_cgi_app(endpoints):
    """
    Создать CGI приложение с эндпоинтами

    Args:
        endpoints: Список эндпоинтов

    Returns:
        Flask: Настроенное CGI приложение
    """
    app = create_app()

    # Инициализация расширения плагина
    mgr_addon = MgrAddonExtension()
    mgr_addon.init_app(app, endpoints)

    return app


def create_cli_app():
    """
    Создать CLI приложение

    Returns:
        Flask: Настроенное CLI приложение
    """
    app = create_app()
    return app


# Экспорт основных компонентов
__all__ = ["MgrAddonExtension", "get_router", "create_app", "create_cgi_app", "create_cli_app"]
