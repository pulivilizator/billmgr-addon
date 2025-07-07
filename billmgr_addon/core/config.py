# -*- coding: utf-8 -*-

"""
Система конфигурации для плагинов
"""

import os
import sys
from pathlib import Path
from typing import Any, Dict, Optional

import tomlkit


def get_project_root() -> Path:
    """
    Определяет корневую директорию проекта.
    """
    try:
        current_dir = os.getcwd()
        if current_dir not in sys.path:
            sys.path.insert(0, current_dir)

        import settings

        if hasattr(settings, "PROJECT_ROOT"):
            project_root = Path(settings.PROJECT_ROOT)
            if project_root.is_absolute():
                return project_root
            else:
                return Path(current_dir) / project_root

        settings_file = Path(settings.__file__)
        return settings_file.parent

    except ImportError:
        pass

    project_root_env = os.getenv("BILLMGR_ADDON_PROJECT_ROOT")
    if project_root_env:
        return Path(project_root_env)

    return Path(os.getcwd())


def get_config_path() -> Path:
    """
    Определяет путь к файлу конфигурации.

    """
    try:
        current_dir = os.getcwd()
        if current_dir not in sys.path:
            sys.path.insert(0, current_dir)

        import settings

        if hasattr(settings, "CONFIG_PATH"):
            config_path = Path(settings.CONFIG_PATH)
            if config_path.is_absolute():
                return config_path
            else:
                return get_project_root() / config_path

    except ImportError:
        pass

    return get_project_root() / "config.toml"


def get_public_path() -> Path:
    """
    Определяет путь к директории public.
    """
    try:
        current_dir = os.getcwd()
        if current_dir not in sys.path:
            sys.path.insert(0, current_dir)

        import settings

        if hasattr(settings, "PUBLIC_PATH"):
            public_path = Path(settings.PUBLIC_PATH)
            if public_path.is_absolute():
                return public_path
            else:
                return get_project_root() / public_path

    except ImportError:
        pass

    return get_project_root() / "public"


def get_logs_path() -> Path:
    """
    Определяет путь к директории logs.
    """
    try:
        current_dir = os.getcwd()
        if current_dir not in sys.path:
            sys.path.insert(0, current_dir)

        import settings

        if hasattr(settings, "LOGS_PATH"):
            logs_path = Path(settings.LOGS_PATH)
            if logs_path.is_absolute():
                return logs_path
            else:
                return get_project_root() / logs_path

    except ImportError:
        pass

    return get_project_root() / "logs"


_project_root: Optional[Path] = None
_config_path: Optional[Path] = None
_public_path: Optional[Path] = None
_logs_path: Optional[Path] = None


def get_project_root_cached() -> Path:
    """Кешированная версия get_project_root()"""
    global _project_root
    if _project_root is None:
        _project_root = get_project_root()
    return _project_root


def get_config_path_cached() -> Path:
    """Кешированная версия get_config_path()"""
    global _config_path
    if _config_path is None:
        _config_path = get_config_path()
    return _config_path


def get_public_path_cached() -> Path:
    """Кешированная версия get_public_path()"""
    global _public_path
    if _public_path is None:
        _public_path = get_public_path()
    return _public_path


def get_logs_path_cached() -> Path:
    """Кешированная версия get_logs_path()"""
    global _logs_path
    if _logs_path is None:
        _logs_path = get_logs_path()
    return _logs_path


def get_cwd_path():
    return get_project_root_cached()


def get_config_path_global():
    return get_config_path_cached()


def get_public_path_global():
    return get_public_path_cached()


def get_logs_path_global():
    return get_logs_path_cached()


class _LazyPath:
    def __init__(self, func):
        self._func = func
        self._value = None

    def __fspath__(self):
        if self._value is None:
            self._value = self._func()
        return str(self._value)

    def __str__(self):
        return self.__fspath__()

    def __repr__(self):
        return f"LazyPath({self.__fspath__()})"


cwd_path = _LazyPath(get_project_root_cached)
config_path = _LazyPath(get_config_path_cached)
public_path = _LazyPath(get_public_path_cached)
logs_path = _LazyPath(get_logs_path_cached)


def load_config() -> dict:
    """Загружает конфигурацию из файла"""
    config_file = get_config_path_cached()

    if not config_file.exists():
        return {}

    try:
        with open(config_file, "r", encoding="utf-8") as f:
            return tomlkit.load(f)
    except Exception as e:
        print(f"Ошибка загрузки конфигурации из {config_file}: {e}")
        return {}


class Config:
    """
    Класс для работы с конфигурацией плагина

    Поддерживает загрузку из TOML файлов и переменных окружения.
    """

    def __init__(self, config_path: Optional[Path] = None):
        self.config_path = config_path or get_config_path()
        self.data = {}
        self._load_config()

    def _load_config(self):
        if self.config_path.exists():
            try:
                with open(self.config_path, "r", encoding="utf-8") as f:
                    self.data = tomlkit.load(f)
            except Exception as e:
                print(f"Error loading config from {self.config_path}: {e}")

    def get(self, key: str, default: Any = None) -> Any:
        env_key = key.upper().replace(".", "_")
        env_value = os.getenv(env_key)
        if env_value is not None:
            return self._convert_env_value(env_value)

        keys = key.split(".")
        current = self.data

        for k in keys:
            if isinstance(current, dict) and k in current:
                current = current[k]
            else:
                return default

        return current

    def _convert_env_value(self, value: str) -> Any:
        if value.lower() in ("true", "yes", "1", "on"):
            return True
        elif value.lower() in ("false", "no", "0", "off"):
            return False

        try:
            return int(value)
        except ValueError:
            pass

        try:
            return float(value)
        except ValueError:
            pass

        return value

    def set(self, key: str, value: Any):
        keys = key.split(".")
        current = self.data

        for k in keys[:-1]:
            if not isinstance(current, dict):
                return
            if k not in current:
                current[k] = {}
            current = current[k]

        if isinstance(current, dict):
            current[keys[-1]] = value

    def save(self):
        self.config_path.parent.mkdir(parents=True, exist_ok=True)

        with open(self.config_path, "w", encoding="utf-8") as f:
            tomlkit.dump(self.data, f)

    def update_from_dict(self, config_dict: Dict[str, Any]):
        self.data.update(config_dict)

    def to_dict(self) -> Dict[str, Any]:
        return dict(self.data)


_config = None


def get_config() -> Config:
    """Получить глобальный экземпляр конфигурации"""
    global _config
    if _config is None:
        _config = Config()
    return _config


__all__ = [
    "Config",
    "get_config",
    "get_project_root",
    "get_config_path",
    "get_logs_path",
    "get_public_path",
    "get_project_root_cached",
    "get_config_path_cached",
    "get_logs_path_cached",
    "get_public_path_cached",
    "load_config",
    "cwd_path",
    "config_path",
    "public_path",
    "logs_path",
]
