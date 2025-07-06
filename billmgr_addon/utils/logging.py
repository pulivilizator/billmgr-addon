# -*- coding: utf-8 -*-

import logging
import sys
from logging.handlers import RotatingFileHandler
from pathlib import Path
from typing import Optional, Union

LOGGER_NAME = "billmgr_addon"
LOGGER = None


def _create_default_logger():
    """Создать дефолтный логгер для пакета (без вывода в STDOUT)"""
    logger = logging.getLogger(LOGGER_NAME)

    if logger.handlers and logger.level != logging.NOTSET:
        return logger

    logger.setLevel(logging.DEBUG)

    # Убираем вывод в STDOUT по умолчанию для совместимости с BILLmanager
    # Логгер будет настроен позже через setup_logger или переназначение
    logger.propagate = False

    return logger


LOGGER = _create_default_logger()


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
    enable_file: bool = True,
) -> logging.Logger:
    """
    Настроить логгер для плагина

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

    if name:
        logger = logging.getLogger(name)
        logger.propagate = False
    else:
        logger = logging.getLogger()

    if remove_default_handlers:
        for handler in list(logger.handlers):
            logger.removeHandler(handler)

    log_level = logging.DEBUG if debug else level
    logger.setLevel(log_level)

    detailed_format = "%(asctime)s %(levelname)s: %(message)s [in %(pathname)s:%(lineno)d]"
    simple_format = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    console_format = "%(levelname)s: %(message)s"

    if enable_file:
        if path is None:
            # Используем новую систему определения путей через settings.py
            try:
                from billmgr_addon.core.config import get_logs_path_cached
                logs_path = get_logs_path_cached()
            except ImportError:
                # Fallback на старую систему если новая не доступна
                base_path = Path.cwd()
                logs_path = base_path / "logs"
        elif isinstance(path, str):
            if Path(path).is_absolute():
                logs_path = Path(path)
            else:
                # Используем новую систему для относительных путей
                try:
                    from billmgr_addon.core.config import get_project_root_cached
                    project_root = get_project_root_cached()
                    logs_path = project_root / path
                except ImportError:
                    # Fallback на старую систему
                    logs_path = Path.cwd() / path
        else:
            logs_path = Path(path)

        logs_path.mkdir(parents=True, exist_ok=True)

        log_filename = Path(filename).name
        if not log_filename or log_filename != filename:
            raise ValueError(f"Invalid filename '{filename}' argument")

        file_handler = RotatingFileHandler(
            logs_path / log_filename, maxBytes=max_bytes, backupCount=backup_count, encoding="utf-8"
        )
        file_handler.setFormatter(logging.Formatter(detailed_format))
        file_handler.setLevel(log_level)
        logger.addHandler(file_handler)

    if enable_console:
        console_handler = None

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


__all__ = [
    "setup_logger",
    "LOGGER",
    "LOGGER_NAME",
]
