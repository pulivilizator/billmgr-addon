#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Пример WSGI файла для развертывания BILLmanager плагина

Для запуска:
- Gunicorn: gunicorn -w 4 wsgi:app
- uWSGI: uwsgi --http :8000 --wsgi-file wsgi.py --callable app
"""

from pathlib import Path

from billmgr_addon import create_wsgi_app

# Путь к директории с плагином
plugin_path = Path(__file__).parent

# Создаем WSGI приложение
# Можно указать имя плагина, если он установлен как пакет
# app = create_wsgi_app(plugin_name='my_plugin')

# Или использовать локальный модуль
app = create_wsgi_app(
    plugin_name="example_plugin",  # Имя модуля с эндпоинтами
    plugin_path=plugin_path,  # Путь к плагину
    config_path=plugin_path / "config.toml",  # Путь к конфигурации (опционально)
)

# Альтернативный способ - передать эндпоинты напрямую
# from example_plugin import endpoints
# from billmgr_addon import create_wsgi_app_from_endpoints
# app = create_wsgi_app_from_endpoints(endpoints)

# Для локальной разработки
if __name__ == "__main__":
    # Получаем Flask приложение для запуска встроенного сервера
    flask_app = app.create_app()
    flask_app.run(
        host="127.0.0.1",
        port=8000,
        debug=True,
        # Отключаем reloader для избежания проблем с импортами
        use_reloader=False,
    )
