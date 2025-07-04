# -*- coding: utf-8 -*-

"""
Система конфигурации для плагинов
"""

import os
from pathlib import Path
from typing import Any, Dict, Optional

import tomlkit


class Config:
    """
    Класс для работы с конфигурацией плагина

    Поддерживает загрузку из TOML файлов и переменных окружения.
    """

    def __init__(self, config_path: Optional[Path] = None):
        self.config_path = config_path or Path("config.toml")
        self.data = {}
        self._load_config()

    def _load_config(self):
        """Загрузить конфигурацию из файла"""
        if self.config_path.exists():
            try:
                with open(self.config_path, "r", encoding="utf-8") as f:
                    self.data = tomlkit.load(f)
            except Exception as e:
                print(f"Error loading config from {self.config_path}: {e}")

    def get(self, key: str, default: Any = None) -> Any:
        """
        Получить значение конфигурации

        Поддерживает точечную нотацию для вложенных значений.
        Сначала проверяет переменные окружения, затем конфигурационный файл.

        Args:
            key: Ключ конфигурации
            default: Значение по умолчанию

        Returns:
            Any: Значение конфигурации
        """
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
        """Конвертировать значение из переменной окружения"""
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
        """Установить значение конфигурации"""
        keys = key.split(".")
        current = self.data

        for k in keys[:-1]:
            if k not in current:
                current[k] = {}
            current = current[k]

        current[keys[-1]] = value

    def save(self):
        """Сохранить конфигурацию в файл"""
        self.config_path.parent.mkdir(parents=True, exist_ok=True)

        with open(self.config_path, "w", encoding="utf-8") as f:
            tomlkit.dump(self.data, f)

    def update_from_dict(self, config_dict: Dict[str, Any]):
        """Обновить конфигурацию из словаря"""
        self.data.update(config_dict)

    def to_dict(self) -> Dict[str, Any]:
        """Получить конфигурацию как словарь"""
        return dict(self.data)


def create_default_config() -> Dict[str, Any]:
    """Создать конфигурацию по умолчанию"""
    return {
        "debug": False,
        "secret_key": "change-me-in-production",
        "billmgr": {
            "api_url": "https://localhost:1500/billmgr",
            "api_interface": "",
            "forwarded_secret": "SECRET_FROM_BILLMGR_CONF",
        },
        "database": {
            "host": "localhost",
            "port": 3306,
            "name": "billmgr",
            "user": "billmgr",
            "password": "",
            "charset": "utf8mb4",
        },
        "logging": {
            "level": "INFO",
            "format": "%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        },
        "plugin": {
            "name": "My Plugin",
            "version": "1.0.0",
            "description": "BILLmanager plugin",
        },
    }


def init_config_from_flask(app, config: Config):
    """
    Инициализировать Flask приложение из конфигурации

    Args:
        app: Flask приложение
        config: Экземпляр конфигурации
    """
    app.config["DEBUG"] = config.get("debug", False)
    app.config["SECRET_KEY"] = config.get("secret_key", "change-me-in-production")

    app.config["BILLMGR_API_URL"] = config.get("billmgr.api_url")
    app.config["BILLMGR_API_USE_INTERFACE"] = config.get("billmgr.api_interface")
    app.config["FORWARDED_SECRET"] = config.get("billmgr.forwarded_secret")

    app.config["DB_HOST"] = config.get("database.host")
    app.config["DB_PORT"] = config.get("database.port")
    app.config["DB_NAME"] = config.get("database.name")
    app.config["DB_USER"] = config.get("database.user")
    app.config["DB_PASSWORD"] = config.get("database.password")
    app.config["DB_CHARSET"] = config.get("database.charset")


_config = None


def get_config() -> Config:
    """Получить глобальный экземпляр конфигурации"""
    global _config
    if _config is None:
        _config = Config()
    return _config


__all__ = ["Config", "create_default_config", "init_config_from_flask", "get_config"]
