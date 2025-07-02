# -*- coding: utf-8 -*-

import logging
import sys
from pathlib import Path
from logging.handlers import RotatingFileHandler
from typing import Union, Optional

try:
    from flask import current_app
    from werkzeug.local import LocalProxy
    
    # Flask logger proxy - доступен только если Flask активен
    flask_logger = LocalProxy(lambda: current_app.logger)
    
    # Flask-совместимый логгер (аналогично плагину ресселлинга)
    flask_compatible_logger = LocalProxy(lambda: current_app.logger)
    
except ImportError:
    flask_logger = None
    flask_compatible_logger = None


# ===== ВНУТРЕННИЙ ЛОГГЕР ПАКЕТА (НОВЫЙ ПОДХОД) =====

# Создаем простой консольный логгер по умолчанию
def _create_default_logger():
    """Создать дефолтный консольный логгер для пакета"""
    logger = logging.getLogger("billmgr_addon")
    logger.setLevel(logging.INFO)
    
    # Если обработчики уже есть, не добавляем повторно
    if not logger.handlers:
        handler = logging.StreamHandler(sys.stdout)
        formatter = logging.Formatter("billmgr_addon: %(levelname)s - %(message)s")
        handler.setFormatter(formatter)
        logger.addHandler(handler)
        logger.propagate = False
    
    return logger


# Внутренний логгер пакета - простая переменная которую можно переназначить
LOGGER = _create_default_logger()


# ===== ГЛОБАЛЬНЫЙ ЛОГГЕР (универсальный подход) =====

# Глобальный логгер по аналогии с плагином ресселлинга
# Инициализируется лениво при первом обращении
_global_logger = None


def get_global_logger():
    """Получить глобальный логгер приложения"""
    global _global_logger
    if _global_logger is None:
        # Инициализируем дефолтный логгер если не был настроен
        _global_logger = setup_development_logging("billmgr_addon")
    return _global_logger


def set_global_logger(logger_instance):
    """Установить глобальный логгер приложения"""
    global _global_logger
    _global_logger = logger_instance


# Ленивый глобальный логгер для импорта
class LazyLogger:
    """Ленивый логгер который инициализируется при первом обращении"""
    
    def __getattr__(self, name):
        # При первом обращении создаем реальный логгер
        real_logger = get_global_logger()
        # Заменяем себя на реальный логгер в глобальном пространстве
        globals()['logger'] = real_logger
        return getattr(real_logger, name)

logger = LazyLogger()


def setup_logger(
    name: Optional[str] = None,
    path: Union[Path, str, None] = None,
    filename: str = "app.log",
    level: int = logging.INFO,
    debug: bool = False,
    remove_default_handlers: bool = False,
    max_bytes: int = 1024 * 1024 * 10,  # 10MB
    backup_count: int = 5,
    enable_console: bool = True,
    enable_file: bool = True
) -> logging.Logger:
    """
    Настроить продвинутый логгер для BILLmanager плагина

    Args:
        name: Имя логгера (если None - используется root logger)
        path: Путь к папке с логами (по умолчанию ./logs)
        filename: Имя файла лога
        level: Уровень логирования
        debug: Режим отладки (включает DEBUG level)
        remove_default_handlers: Удалить существующие обработчики
        max_bytes: Максимальный размер файла лога (для ротации)
        backup_count: Количество резервных файлов
        enable_console: Включить вывод в консоль
        enable_file: Включить вывод в файл

    Returns:
        logging.Logger: Настроенный логгер
    """
    
    # Определяем логгер
    if name:
        logger = logging.getLogger(name)
        logger.propagate = False
    else:
        logger = logging.getLogger()
    
    # Удаляем существующие обработчики если нужно
    if remove_default_handlers:
        for handler in list(logger.handlers):
            logger.removeHandler(handler)
    
    # Определяем уровень логирования
    log_level = logging.DEBUG if debug else level
    logger.setLevel(log_level)
    
    # Форматы логирования
    detailed_format = "%(asctime)s %(levelname)s: %(message)s [in %(pathname)s:%(lineno)d]"
    simple_format = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    console_format = "%(levelname)s: %(message)s"
    
    # Настройка файлового логгирования
    if enable_file:
        # Определяем путь к логам
        if path is None:
            # По умолчанию создаем папку logs в корне проекта
            base_path = Path.cwd()
            logs_path = base_path / "logs"
        elif isinstance(path, str):
            if Path(path).is_absolute():
                logs_path = Path(path)
            else:
                logs_path = Path.cwd() / path
        else:
            logs_path = Path(path)
        
        # Создаем папку если её нет
        logs_path.mkdir(parents=True, exist_ok=True)
        
        # Валидация имени файла
        log_filename = Path(filename).name
        if not log_filename or log_filename != filename:
            raise ValueError(f"Invalid filename '{filename}' argument")
        
        # Создаем файловый обработчик с ротацией
        file_handler = RotatingFileHandler(
            logs_path / log_filename,
            maxBytes=max_bytes,
            backupCount=backup_count,
            encoding="utf-8"
        )
        file_handler.setFormatter(logging.Formatter(detailed_format))
        file_handler.setLevel(log_level)
        logger.addHandler(file_handler)
    
    # Настройка консольного логгирования
    if enable_console:
        # Определяем тип консольного вывода
        console_handler = None
        
        # Для Flask команд используем простой формат
        if sys.argv and len(sys.argv) > 0:
            script_name = sys.argv[0].split("/")[-1]
            if script_name in ["flask", "gunicorn", "uwsgi"]:
                console_handler = logging.StreamHandler(sys.stdout)
                console_handler.setFormatter(logging.Formatter(console_format))
            else:
                console_handler = logging.StreamHandler()
                console_handler.setFormatter(logging.Formatter(simple_format))
        else:
            console_handler = logging.StreamHandler()
            console_handler.setFormatter(logging.Formatter(simple_format))
        
        if console_handler:
            console_handler.setLevel(log_level)
            logger.addHandler(console_handler)
    
    return logger


def get_flask_logger():
    """
    Получить Flask logger если доступен
    
    Returns:
        Logger или None если Flask не активен
    """
    return flask_logger


def setup_production_logging(
    app_name: str,
    log_dir: Union[str, Path] = "/var/log/billmgr-addons",
    debug: bool = False
) -> logging.Logger:
    """
    Настроить логгирование для продакшен окружения
    
    Args:
        app_name: Название приложения (используется в имени файла)
        log_dir: Директория для логов
        debug: Режим отладки
    
    Returns:
        logging.Logger: Настроенный логгер
    """
    return setup_logger(
        name=app_name,
        path=log_dir,
        filename=f"{app_name}.log",
        debug=debug,
        remove_default_handlers=True,
        max_bytes=1024 * 1024 * 50,  # 50MB для продакшена
        backup_count=10,
        enable_console=False,  # В продакшене только файлы
        enable_file=True
    )


def setup_development_logging(
    app_name: str = "development",
    debug: bool = True
) -> logging.Logger:
    """
    Настроить логгирование для разработки
    
    Args:
        app_name: Название приложения
        debug: Режим отладки (по умолчанию True)
    
    Returns:
        logging.Logger: Настроенный логгер
    """
    return setup_logger(
        name=app_name,
        path="logs",
        filename=f"{app_name}.log",
        debug=debug,
        enable_console=True,
        enable_file=True
    )


# ===== FLASK-СОВМЕСТИМЫЕ ФУНКЦИИ =====

def setup_flask_logging(app, debug: Optional[bool] = None):
    """
    Настроить логгирование для Flask приложения (аналогично плагину ресселлинга)
    
    Args:
        app: Flask приложение
        debug: Режим отладки (если None - берется из app.config['DEBUG'])
    
    Returns:
        logging.Logger: Flask логгер приложения
    """
    debug_mode = debug if debug is not None else app.config.get('DEBUG', False)
    
    # Настраиваем root логгер
    root_logger = setup_logger(
        name=None,  # root logger
        path="logs", 
        filename="app.log",
        debug=debug_mode,
        remove_default_handlers=True
    )
    
    # Настраиваем логгер приложения
    app_logger = setup_logger(
        name=app.name,
        path="logs",
        filename=f"{app.name}.log", 
        debug=debug_mode,
        remove_default_handlers=True
    )
    
    # Flask автоматически использует логгер с именем app.name как app.logger
    return app_logger


def get_flask_compatible_logger():
    """
    Получить Flask-совместимый логгер (аналогично app.logging import logger)
    
    Returns:
        LocalProxy или None если Flask не доступен
    """
    return flask_compatible_logger


# Для обратной совместимости
def get_logger(name: str) -> logging.Logger:
    """
    Получить простой логгер (для обратной совместимости)
    
    Args:
        name: Имя логгера
    
    Returns:
        logging.Logger: Логгер
    """
    return setup_logger(name=name, enable_file=False)


__all__ = [
    # Основные функции логгирования для плагинов
    "setup_logger",
    "get_flask_logger", 
    "setup_production_logging",
    "setup_development_logging",
    "get_logger",  # Для обратной совместимости
    "logger",  # Глобальный логгер
    "set_global_logger",  # Для настройки глобального логгера
    "get_global_logger",  # Для получения глобального логгера
    "setup_flask_logging",
    "get_flask_compatible_logger",
    
    # Внутренний логгер пакета (новый простой подход)
    "LOGGER",  # Переменная логгера пакета для переназначения
]
