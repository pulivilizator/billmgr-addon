 # -*- coding: utf-8 -*-

import logging
import xml.etree.ElementTree as ET
from flask import request as flask_request
from flask_login import current_user


class MgrRequest:
    """
    Класс для работы с MGR запросами от BILLmanager
    
    Обрабатывает данные, передаваемые через переменные окружения CGI.
    """
    
    def __init__(self, environ):
        self.environ = environ
        self.params = {}
        self.xml_input = None
        self.auth_level = None
        self.user_api = None
        
        self._parse_environ()

    def _parse_environ(self):
        """Парсинг переменных окружения"""
        # Извлечение параметров
        query_string = self.environ.get('QUERY_STRING', '')
        if query_string:
            import urllib.parse
            self.params = dict(urllib.parse.parse_qsl(query_string))
        
        # Извлечение XML данных
        content_length = self.environ.get('CONTENT_LENGTH')
        if content_length:
            try:
                content_length = int(content_length)
                if content_length > 0:
                    # В реальной CGI среде данные читаются из stdin
                    # Здесь упрощенная версия
                    pass
            except (ValueError, TypeError):
                pass
        
        # Уровень авторизации
        self.auth_level = self.environ.get('AUTH_LEVEL')
        if self.auth_level:
            try:
                self.auth_level = int(self.auth_level)
            except (ValueError, TypeError):
                self.auth_level = None

    def init_user_api(self, api_url, interface=None, default_remote_address=None, default_forwarded_secret=None):
        """Инициализация API клиента пользователя"""
        # Здесь будет инициализация API клиента
        # Пока заглушка
        pass

    def get_param(self, name, default=None):
        """Получить параметр запроса"""
        return self.params.get(name, default)


class CgiRequest:
    """
    Класс для работы с CGI запросами
    
    Обрабатывает обычные HTTP запросы к плагину.
    """
    
    def __init__(self, request=None):
        self.request = request or flask_request
        self.func = self.request.args.get('func')
        self.method = self.request.method
        self.user = None
        self.params = {}
        
        self._parse_request()

    def _parse_request(self):
        """Парсинг HTTP запроса"""
        # GET параметры
        self.params.update(self.request.args)
        
        # POST данные
        if self.request.method == 'POST':
            if self.request.is_json:
                self.params.update(self.request.json or {})
            else:
                self.params.update(self.request.form)

    def get_param(self, name, default=None):
        """Получить параметр запроса"""
        return self.params.get(name, default)

    def __repr__(self):
        return f"CgiRequest(func={self.func}, method={self.method}, params={self.params})"


__all__ = ['MgrRequest', 'CgiRequest']