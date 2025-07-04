# -*- coding: utf-8 -*-

import os
from pathlib import Path
from typing import Optional, Union

def get_project_root() -> Path:
    """
    Определяем корневую директорию проекта с приоритетами:
    1. Переменная окружения BILLMGR_ADDON_PROJECT_ROOT
    2. Поиск по структуре проекта (config.toml + xml/ + app/)
    3. Текущая рабочая директория (fallback)
    """
    # 1. Проверяем переменную окружения
    env_project_root = os.environ.get('BILLMGR_ADDON_PROJECT_ROOT')
    if env_project_root:
        return Path(env_project_root).resolve()
    
    # 2. Ищем по структуре проекта
    current = Path.cwd()
    while current != current.parent:
        if ((current / "config.toml").exists() and 
            (current / "xml").exists() and 
            (current / "app").exists()):
            return current
        current = current.parent
    
    # 3. Fallback на текущую директорию
    return Path.cwd()

# Базовые пути для проекта
cwd_path = get_project_root()
interpreter_path = cwd_path.joinpath("venv/bin/python3")
config_path = cwd_path.joinpath("config.toml")
public_path = cwd_path.joinpath("public")
xml_path = cwd_path.joinpath("xml")
cgi_app_path = cwd_path.joinpath("cgi.py")
cli_app_path = cwd_path.joinpath("cli.py")
xml_build_path = xml_path.joinpath("build.xml")

# Пути BILLmanager
mgr_path = Path("/usr/local/mgr5")
mgr_plugin_handlers_path = mgr_path.joinpath("addon")
mgr_cgi_handlers_path = mgr_path.joinpath("cgi")
mgr_xml_path = mgr_path.joinpath("etc/xml")


def _create_executable_file(path: Union[Path, str], text: str) -> None:
    file_descriptor = os.open(path=path, flags=(os.O_WRONLY | os.O_CREAT | os.O_TRUNC), mode=0o755)
    with open(file_descriptor, "w") as fh:
        fh.write(text)


def _create_cli_app_link(
    link_path: Union[Path, str],
    app_path: Union[Path, str],
    server_interpreter_path: Optional[Union[Path, str]] = None,
    server_app_path: Optional[Union[Path, str]] = None,
) -> None:
    """
    Создать bash-скрипт для запуска CLI приложения

    Args:
        link_path: Путь к создаваемому скрипту
        app_path: Путь к Python приложению (локальный)
        server_interpreter_path: Путь к интерпретатору на сервере
        server_app_path: Путь к приложению на сервере
    """
    actual_interpreter = server_interpreter_path or interpreter_path
    actual_app_path = server_app_path or app_path

    file_content = f"""#!/bin/bash
export PYTHONIOENCODING=utf-8
export LANG=ru_RU.UTF-8
{actual_interpreter} {actual_app_path} "$@"
"""
    _create_executable_file(link_path, file_content)


def _create_cgi_handler_link(
    link_path: Union[Path, str], server_app_folder: Optional[Union[Path, str]] = None
) -> None:
    """
    Создать bash-скрипт для CGI обработчика

    Args:
        link_path: Путь к создаваемому скрипту
        server_app_folder: Путь к папке приложения на сервере
    """
    if server_app_folder:
        server_app_folder = Path(server_app_folder)
        actual_interpreter = server_app_folder / "venv/bin/python3"
        actual_cgi_app = server_app_folder / "cgi.py"
    else:
        actual_interpreter = interpreter_path
        actual_cgi_app = cgi_app_path

    file_content = f"""#!/bin/bash
export FLASK_APP="{actual_cgi_app}"
export PYTHONIOENCODING=utf-8
export LANG=ru_RU.UTF-8
{actual_interpreter} {actual_cgi_app}
"""
    _create_executable_file(link_path, file_content)


def create_plugin_app_link(
    plugin_name: str, server_app_folder: Optional[Union[Path, str]] = None
) -> Path:
    link_path = mgr_plugin_handlers_path.joinpath(plugin_name)
    _create_cgi_handler_link(link_path, server_app_folder)
    return link_path


def create_cgi_app_link(
    plugin_name: str, server_app_folder: Optional[Union[Path, str]] = None
) -> Path:
    link_path = mgr_cgi_handlers_path.joinpath(plugin_name)
    _create_cgi_handler_link(link_path, server_app_folder)
    return link_path


def create_plugin_xml_symlink(
    plugin_name: str, server_xml_build_path: Optional[Union[Path, str]] = None
) -> Path:
    link_path = mgr_xml_path.joinpath(f"billmgr_mod_{plugin_name}.xml")
    if link_path.is_symlink():
        link_path.unlink()

    actual_xml_path = server_xml_build_path or xml_build_path
    link_path.symlink_to(actual_xml_path)
    return link_path


def create_plugin_symlinks(
    plugin_name: str, server_app_folder: Optional[Union[Path, str]] = None
) -> dict:
    server_xml_build_path = None
    if server_app_folder:
        server_xml_build_path = Path(server_app_folder) / "xml/build.xml"

    return {
        "addon_link": create_plugin_app_link(plugin_name, server_app_folder),
        "cgi_link": create_cgi_app_link(plugin_name, server_app_folder),
        "xml_link": create_plugin_xml_symlink(plugin_name, server_xml_build_path),
    }


def get_standard_paths(project_root: Union[Path, str, None] = None) -> dict:
    if project_root is None:
        project_root = cwd_path
    else:
        project_root = Path(project_root)

    return {
        "cwd_path": project_root,
        "interpreter_path": project_root / "venv/bin/python3",
        "config_path": project_root / "config.toml",
        "public_path": project_root / "public",
        "xml_path": project_root / "xml",
        "cgi_app_path": project_root / "cgi.py",
        "cli_app_path": project_root / "cli.py",
        "xml_build_path": project_root / "xml/build.xml",
    }


def get_mgr_paths() -> dict:
    return {
        "mgr_path": mgr_path,
        "mgr_plugin_handlers_path": mgr_plugin_handlers_path,
        "mgr_cgi_handlers_path": mgr_cgi_handlers_path,
        "mgr_xml_path": mgr_xml_path,
    }
