 #!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
CGI интерфейс для BILLmanager плагинов

Универсальный CGI обработчик, который может быть использован любым плагином.
"""

import os
import sys
import logging
from pathlib import Path


def run_with_cgi(application):
    """
    Запуск WSGI приложения в CGI режиме
    
    Адаптировано из исходного cloud-infrastructure-reselling-addon/cgi.py
    """
    environ = dict(os.environ.items())
    environ['wsgi.input'] = sys.stdin.buffer
    environ['wsgi.errors'] = sys.stderr
    environ['wsgi.version'] = (1, 0)
    environ['wsgi.multithread'] = False
    environ['wsgi.multiprocess'] = True
    environ['wsgi.run_once'] = True

    if environ.get('HTTPS', 'off') in ('on', '1'):
        environ['wsgi.url_scheme'] = 'https'
    else:
        environ['wsgi.url_scheme'] = 'http'

    headers_set = []
    headers_sent = []

    is_plugin_request = environ.get('EVENT_TYPE') in ['action', 'before', 'after']

    def write(data):
        if not headers_set:
            raise AssertionError("write() before start_response()")

        if not is_plugin_request and not headers_sent:
            # Before the first output, send the stored headers
            status, response_headers = headers_sent[:] = headers_set
            sys.stdout.write(f'HTTP/1.1 {status}\r\n')
            for header in response_headers:
                sys.stdout.write('{}: {}\r\n'.format(header[0], header[1]))
            sys.stdout.write('\r\n')

        response_body = data.decode('utf-8')
        sys.stdout.write(response_body)

    def start_response(status, response_headers, exception=None):
        if exception:
            try:
                if headers_sent:
                    # Re-raise original exception if headers sent
                    raise exception
            finally:
                exception = None     # avoid dangling circular ref
        elif headers_set:
            raise AssertionError("Headers already set!")

        headers_set[:] = [status, response_headers]
        return write

    try:
        result = application(environ, start_response)
    except Exception as e:
        # Логирование ошибок
        from billmgr_addon.utils.logging import get_logger
        logger = get_logger('cgi', remove_default_handlers=True)
        logger.exception(e)
        
        headers_set = []
        headers_sent = []
        start_response('500 Internal Server Error', [('Content-Type', 'text/plain')])
        write('Internal Server Error'.encode('utf-8'))
        sys.exit(1)
        
    try:
        for data in result:
            if data:    # don't send headers until body appears
                write(data)
        if not headers_sent:
            write(b'')   # send headers now if body was empty
    finally:
        if hasattr(result, 'close'):
            result.close()
            
    sys.exit(0)


def create_cgi_app_from_module(module_name):
    """
    Создать CGI приложение из модуля проекта
    
    Args:
        module_name: Имя модуля проекта (например, 'my_plugin')
    """
    try:
        # Импортируем модуль проекта
        project_module = __import__(module_name)
        
        # Пробуем найти функцию создания CGI приложения
        if hasattr(project_module, 'create_cgi_app'):
            return project_module.create_cgi_app()
        elif hasattr(project_module, 'app'):
            return project_module.app
        else:
            raise ImportError(f"Module {module_name} doesn't have 'create_cgi_app' function or 'app' object")
            
    except ImportError as e:
        # Fallback - создаем простое приложение
        from billmgr_addon import create_cgi_app
        return create_cgi_app([])


def main():
    """Главная функция CGI интерфейса"""
    # Определяем имя проекта из переменной окружения или из директории
    project_name = os.environ.get('PLUGIN_NAME')
    
    if not project_name:
        # Пробуем определить из текущей директории
        cwd = Path.cwd()
        if (cwd / 'setup.py').exists():
            # Читаем setup.py чтобы найти имя пакета
            try:
                import re
                setup_content = (cwd / 'setup.py').read_text()
                match = re.search(r"name=['\"]([^'\"]+)['\"]", setup_content)
                if match:
                    project_name = match.group(1).replace('-', '_')
            except:
                pass
        
        if not project_name:
            project_name = cwd.name.replace('-', '_')
    
    # Добавляем текущую директорию в Python path
    sys.path.insert(0, str(Path.cwd()))
    
    try:
        app = create_cgi_app_from_module(project_name)
        run_with_cgi(app)
    except Exception as e:
        # Последний fallback - возвращаем простую ошибку
        print("Content-Type: text/html; charset=utf-8")
        print()
        print(f"<html><body><h1>Plugin Error</h1><p>{e}</p></body></html>")
        sys.exit(1)


if __name__ == '__main__':
    main()