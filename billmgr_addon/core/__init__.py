# -*- coding: utf-8 -*-
"""
Ядро BILLmanager Addon Framework

Содержит основные компоненты для создания плагинов:
- Фабрики приложений
- Эндпоинты и маршрутизация
- UI компоненты
- Обработка запросов и ответов
"""

# Пока просто заглушки для импортов
# Полная реализация будет добавлена позднее

def create_app():
    """Создать основное Flask приложение"""
    from flask import Flask
    app = Flask(__name__)
    return app

def create_cgi_app(endpoints=None):
    """Создать CGI приложение"""
    from flask import Flask
    app = Flask(__name__)
    return app

def create_cli_app():
    """Создать CLI приложение"""
    from flask import Flask
    app = Flask(__name__)
    return app

# Заглушки для классов эндпоинтов
class MgrEndpoint:
    """Базовый класс эндпоинта"""
    def __init__(self, name):
        self.name = name

class ListEndpoint(MgrEndpoint):
    """Эндпоинт для списков"""
    pass

class FormEndpoint(MgrEndpoint):
    """Эндпоинт для форм"""
    pass

class ActionEndpoint(MgrEndpoint):
    """Эндпоинт для действий"""
    pass

class CgiEndpoint(MgrEndpoint):
    """CGI эндпоинт"""
    pass

class DownloadCgiEndpoint(CgiEndpoint):
    """CGI эндпоинт для загрузки файлов"""
    pass

class HtmlCgiEndpoint(CgiEndpoint):
    """CGI эндпоинт для HTML страниц"""
    pass

# Заглушки для UI компонентов
class MgrForm:
    """Компонент формы"""
    pass

class MgrList:
    """Компонент списка"""
    def set_data_rows(self, data):
        """Установить данные строк"""
        pass

class MgrError:
    """Компонент ошибки"""
    pass

class MgrRequest:
    """Запрос от BILLmanager"""
    pass

class MgrRouter:
    """Маршрутизатор запросов"""
    pass

__all__ = [
    'create_app',
    'create_cgi_app', 
    'create_cli_app',
    'MgrEndpoint',
    'ListEndpoint',
    'FormEndpoint',
    'ActionEndpoint',
    'CgiEndpoint',
    'DownloadCgiEndpoint',
    'HtmlCgiEndpoint',
    'MgrForm',
    'MgrList',
    'MgrError',
    'MgrRequest',
    'MgrRouter',
] 