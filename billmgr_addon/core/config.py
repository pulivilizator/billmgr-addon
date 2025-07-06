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
    
    Сначала пытается импортировать settings.py и использовать указанные там пути.
    Если settings.py не найден, использует старую логику с переменными окружения.
    """
    # Пытаемся импортировать settings.py из текущей директории
    try:
        # Добавляем текущую директорию в sys.path если её там нет
        current_dir = os.getcwd()
        if current_dir not in sys.path:
            sys.path.insert(0, current_dir)
        
        import settings
        
        # Если в settings.py указан PROJECT_ROOT, используем его
        if hasattr(settings, 'PROJECT_ROOT'):
            project_root = Path(settings.PROJECT_ROOT)
            if project_root.is_absolute():
                return project_root
            else:
                return Path(current_dir) / project_root
        
        # Если PROJECT_ROOT не указан, используем директорию где лежит settings.py
        settings_file = Path(settings.__file__)
        return settings_file.parent
        
    except ImportError:
        # Если settings.py не найден, используем старую логику
        pass
    
    # Старая логика с переменными окружения
    project_root_env = os.getenv('BILLMGR_ADDON_PROJECT_ROOT')
    if project_root_env:
        return Path(project_root_env)
    
    # Если переменная окружения не установлена, используем текущую директорию
    return Path(os.getcwd())


def get_config_path() -> Path:
    """
    Определяет путь к файлу конфигурации.
    
    Сначала проверяет settings.py, затем использует стандартный путь.
    """
    try:
        # Добавляем текущую директорию в sys.path если её там нет
        current_dir = os.getcwd()
        if current_dir not in sys.path:
            sys.path.insert(0, current_dir)
        
        import settings
        
        # Если в settings.py указан CONFIG_PATH, используем его
        if hasattr(settings, 'CONFIG_PATH'):
            config_path = Path(settings.CONFIG_PATH)
            if config_path.is_absolute():
                return config_path
            else:
                return get_project_root() / config_path
        
    except ImportError:
        pass
    
    # Стандартный путь к конфигурации
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
        
        if hasattr(settings, 'PUBLIC_PATH'):
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
        
        if hasattr(settings, 'LOGS_PATH'):
            logs_path = Path(settings.LOGS_PATH)
            if logs_path.is_absolute():
                return logs_path
            else:
                return get_project_root() / logs_path
        
    except ImportError:
        pass
    
    return get_project_root() / "logs"


# Глобальные переменные инициализируются при первом обращении
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


# Для обратной совместимости оставляем старые переменные, но теперь они вычисляются лениво
# Используем простые функции вместо @property для глобальных переменных
def get_cwd_path():
    return get_project_root_cached()

def get_config_path_global():
    return get_config_path_cached()

def get_public_path_global():
    return get_public_path_cached()

def get_logs_path_global():
    return get_logs_path_cached()

# Для обратной совместимости создаем глобальные переменные через lazy evaluation
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
        with open(config_file, 'r', encoding='utf-8') as f:
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
            if not isinstance(current, dict):
                return  # Не можем установить значение в не-словарь
            if k not in current:
                current[k] = {}
            current = current[k]

        if isinstance(current, dict):
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
