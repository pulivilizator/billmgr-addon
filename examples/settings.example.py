"""
Пример файла settings.py для настройки путей плагина.

Скопируйте этот файл в корневую директорию вашего плагина как settings.py
и настройте пути согласно вашей структуре проекта.
"""

# Корневая директория проекта
# Если указан относительный путь, он будет относительно директории с settings.py
# Если указан абсолютный путь, он будет использован как есть
PROJECT_ROOT = "."

# Путь к файлу конфигурации
# Относительно PROJECT_ROOT, если не абсолютный
CONFIG_PATH = "config.toml"

# Путь к директории с публичными файлами
# Относительно PROJECT_ROOT, если не абсолютный
PUBLIC_PATH = "public"

# Путь к директории с логами
# Относительно PROJECT_ROOT, если не абсолютный
LOGS_PATH = "logs"

# Примеры использования абсолютных путей:
# import os
# PROJECT_ROOT = os.path.dirname(os.path.abspath(__file__))
# CONFIG_PATH = os.path.join(PROJECT_ROOT, "config.toml")
# PUBLIC_PATH = os.path.join(PROJECT_ROOT, "public")
# LOGS_PATH = os.path.join(PROJECT_ROOT, "logs")

# Пример для развертывания в /usr/local/mgr5/addon/myplugin/:
# PROJECT_ROOT = "/usr/local/mgr5/addon/myplugin"
# CONFIG_PATH = "/usr/local/mgr5/addon/myplugin/config.toml"
# PUBLIC_PATH = "/usr/local/mgr5/addon/myplugin/public"
# LOGS_PATH = "/var/log/mgr5/myplugin" 