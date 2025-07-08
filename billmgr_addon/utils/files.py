# -*- coding: utf-8 -*-

import os
from pathlib import Path
from typing import Optional, Union


def get_project_root() -> Path:
    """
    Определение корневой директории проекта
    """
    env_project_root = os.environ.get("BILLMGR_ADDON_PROJECT_ROOT")
    if env_project_root:
        return Path(env_project_root).resolve()

    current = Path.cwd()
    while current != current.parent:
        if (
            (current / "config.toml").exists()
            and (current / "xml").exists()
            and (current / "app").exists()
        ):
            return current
        current = current.parent

    return Path.cwd()


cwd_path = get_project_root()
interpreter_path = cwd_path.joinpath("venv/bin/python3")
config_path = cwd_path.joinpath("config.toml")
public_path = cwd_path.joinpath("public")
xml_path = cwd_path.joinpath("xml")
cgi_app_path = cwd_path.joinpath("cgi.py")
cli_app_path = cwd_path.joinpath("cli.py")
xml_build_path = xml_path.joinpath("build.xml")
processing_module_cli_path = cwd_path.joinpath("processing_module_cli.py")

mgr_path = Path("/usr/local/mgr5")
mgr_plugin_handlers_path = mgr_path.joinpath("addon")
mgr_cgi_handlers_path = mgr_path.joinpath("cgi")
mgr_xml_path = mgr_path.joinpath("etc/xml")
mgr_processing_path = mgr_path.joinpath("processing")


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


def _create_processing_module_script(
    link_path: Union[Path, str], server_app_folder: Optional[Union[Path, str]] = None
) -> None:
    """
    Создать bash-скрипт для processing module

    Args:
        link_path: Путь к создаваемому скрипту
        server_app_folder: Путь к папке приложения на сервере
    """
    if server_app_folder:
        server_app_folder = Path(server_app_folder)
        actual_interpreter = server_app_folder / "venv/bin/python3"
        actual_processing_cli = server_app_folder / "processing_module_cli.py"
    else:
        actual_interpreter = interpreter_path
        actual_processing_cli = processing_module_cli_path

    file_content = f"""#!/bin/bash
export PYTHONIOENCODING=utf-8
export LANG=ru_RU.UTF-8
{actual_interpreter} {actual_processing_cli} "$@"
"""
    _create_executable_file(link_path, file_content)


def create_plugin_processing_module_script(
    plugin_name: str, server_app_folder: Optional[Union[Path, str]] = None
) -> Path:
    """
    Создать processing module script для плагина

    Args:
        plugin_name: Имя плагина
        server_app_folder: Путь к папке приложения на сервере

    Returns:
        Путь к созданному скрипту
    """
    link_path = mgr_processing_path.joinpath(f"pm{plugin_name}")
    _create_processing_module_script(link_path, server_app_folder)
    return link_path


def create_plugin_symlinks(
    plugin_name: str, 
    server_app_folder: Optional[Union[Path, str]] = None,
    install_processing_module: bool = False
) -> dict:
    """
    Создать все ссылки для плагина

    Args:
        plugin_name: Имя плагина
        server_app_folder: Путь к папке приложения на сервере
        install_processing_module: Устанавливать ли processing module script

    Returns:
        Словарь с путями к созданным ссылкам
    """
    server_xml_build_path = None
    if server_app_folder:
        server_xml_build_path = Path(server_app_folder) / "xml/build.xml"

    links = {
        "addon_link": create_plugin_app_link(plugin_name, server_app_folder),
        "cgi_link": create_cgi_app_link(plugin_name, server_app_folder),
        "xml_link": create_plugin_xml_symlink(plugin_name, server_xml_build_path),
    }

    if install_processing_module:
        # Проверяем существование processing_module_cli.py
        processing_cli_exists = False
        if server_app_folder:
            processing_cli_exists = (Path(server_app_folder) / "processing_module_cli.py").exists()
        else:
            processing_cli_exists = processing_module_cli_path.exists()

        if processing_cli_exists:
            links["processing_module_script"] = create_plugin_processing_module_script(plugin_name, server_app_folder)

    return links


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
        "processing_module_cli_path": project_root / "processing_module_cli.py",
    }


def get_mgr_paths() -> dict:
    return {
        "mgr_path": mgr_path,
        "mgr_plugin_handlers_path": mgr_plugin_handlers_path,
        "mgr_cgi_handlers_path": mgr_cgi_handlers_path,
        "mgr_xml_path": mgr_xml_path,
        "mgr_processing_path": mgr_processing_path,
    }
