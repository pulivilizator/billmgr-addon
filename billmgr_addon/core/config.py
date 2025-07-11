# -*- coding: utf-8 -*-

"""
Система конфигурации для плагинов
"""

import os
from functools import lru_cache
from pathlib import Path
from typing import Any, Dict, Optional

import tomlkit


@lru_cache(maxsize=1)
def get_project_root() -> Path:
    """
    Определяет корневую директорию проекта.
    """
    env_project_root = os.getenv("BILLMGR_ADDON_PROJECT_ROOT")
    if env_project_root:
        return Path(env_project_root).resolve()

    current_path = Path.cwd()
    while current_path != current_path.parent:
        if (current_path / "config.toml").exists():
            return current_path
        current_path = current_path.parent
    
    return Path.cwd()


@lru_cache(maxsize=1)
def get_config_path() -> Path:
    """
    Определяет путь к файлу конфигурации.
    """
    return get_project_root() / "config.toml"


@lru_cache(maxsize=1)
def get_public_path() -> Path:
    """
    Определяет путь к директории public.
    
    Возвращает директорию public в корневой директории проекта.
    """
    return get_project_root() / "public"


@lru_cache(maxsize=1)
def get_logs_path() -> Path:
    """
    Определяет путь к директории logs.
    
    Возвращает директорию logs в корневой директории проекта.
    """
    return get_project_root() / "logs"





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


cwd_path = _LazyPath(get_project_root)
config_path = _LazyPath(get_config_path)
public_path = _LazyPath(get_public_path)
logs_path = _LazyPath(get_logs_path)


def load_config() -> dict:
    """Загружает конфигурацию из файла"""
    config_file = get_config_path()

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
    "load_config",
    "cwd_path",
    "config_path",
    "public_path",
    "logs_path",
]
