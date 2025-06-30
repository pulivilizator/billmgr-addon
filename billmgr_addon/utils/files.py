# -*- coding: utf-8 -*-

from pathlib import Path
from typing import Union
import os

# Базовые пути для проекта
cwd_path = Path.cwd()
interpreter_path = cwd_path.joinpath("venv/bin/python3")
config_path = cwd_path.joinpath('config.toml')
public_path = cwd_path.joinpath('public')
xml_path = cwd_path.joinpath('xml')
cgi_app_path = cwd_path.joinpath('cgi.py')
cli_app_path = cwd_path.joinpath('cli.py')
xml_build_path = xml_path.joinpath('build.xml')
processing_module_cli_app_path = cwd_path.joinpath('processing_module_cli.py')
processing_module_xml_path = xml_path.joinpath('processing_module.xml')

# Пути BILLmanager
mgr_path = Path("/usr/local/mgr5")
mgr_plugin_handlers_path = mgr_path.joinpath('addon')
mgr_cgi_handlers_path = mgr_path.joinpath('cgi')
mgr_processing_module_scripts_path = mgr_path.joinpath('processing')
mgr_xml_path = mgr_path.joinpath('etc/xml')


def _create_executable_file(path: Union[Path, str], text: str) -> None:
    """
    Создать исполняемый файл с заданным содержимым
    
    Args:
        path: Путь к файлу
        text: Содержимое файла
    """
    file_descriptor = os.open(
        path=path,
        flags=(os.O_WRONLY | os.O_CREAT | os.O_TRUNC),
        mode=0o755
    )
    with open(file_descriptor, 'w') as fh:
        fh.write(text)


def _create_cli_app_link(link_path: Union[Path, str], app_path: Union[Path, str]) -> None:
    """
    Создать bash-скрипт для запуска CLI приложения
    
    Args:
        link_path: Путь к создаваемому скрипту
        app_path: Путь к Python приложению
    """
    file_content = f"""#!/bin/bash
export PYTHONIOENCODING=utf-8
export LANG=ru_RU.UTF-8
{interpreter_path} {app_path} "$@"
"""
    _create_executable_file(link_path, file_content)


def _create_cgi_handler_link(link_path: Union[Path, str]) -> None:
    """
    Создать bash-скрипт для CGI обработчика
    
    Args:
        link_path: Путь к создаваемому скрипту
    """
    file_content = f"""#!/bin/bash
export FLASK_APP="{cgi_app_path}"
export PYTHONIOENCODING=utf-8
export LANG=ru_RU.UTF-8
{interpreter_path} {cgi_app_path}
"""
    _create_executable_file(link_path, file_content)


def create_plugin_app_link(plugin_name: str) -> Path:
    """
    Создать ссылку на плагин для addon директории
    
    Args:
        plugin_name: Имя плагина
        
    Returns:
        Path: Путь к созданной ссылке
    """
    link_path = mgr_plugin_handlers_path.joinpath(plugin_name)
    _create_cgi_handler_link(link_path)
    return link_path


def create_cgi_app_link(plugin_name: str) -> Path:
    """
    Создать ссылку на CGI приложение
    
    Args:
        plugin_name: Имя плагина
        
    Returns:
        Path: Путь к созданной ссылке
    """
    link_path = mgr_cgi_handlers_path.joinpath(plugin_name)
    _create_cgi_handler_link(link_path)
    return link_path


def create_plugin_xml_symlink(plugin_name: str) -> Path:
    """
    Создать символическую ссылку на XML файл плагина
    
    Args:
        plugin_name: Имя плагина
        
    Returns:
        Path: Путь к созданной ссылке
    """
    link_path = mgr_xml_path.joinpath(f"billmgr_mod_{plugin_name}.xml")
    if link_path.is_symlink():
        link_path.unlink()

    link_path.symlink_to(xml_build_path)
    return link_path


def create_processing_module_xml_symlink(module_name: str) -> Path:
    """
    Создать символическую ссылку на XML файл модуля обработки
    
    Args:
        module_name: Имя модуля
        
    Returns:
        Path: Путь к созданной ссылке
    """
    link_path = mgr_xml_path.joinpath(f"billmgr_mod_pm{module_name}.xml")
    if link_path.is_symlink():
        link_path.unlink()

    link_path.symlink_to(processing_module_xml_path)
    return link_path


def create_processing_module_cli_link(module_name: str) -> Path:
    """
    Создать ссылку на CLI модуля обработки
    
    Args:
        module_name: Имя модуля
        
    Returns:
        Path: Путь к созданной ссылке
    """
    link_path = mgr_processing_module_scripts_path.joinpath(f"pm{module_name}")
    _create_cli_app_link(link_path, processing_module_cli_app_path)
    return link_path


def create_plugin_symlinks(plugin_name: str) -> dict:
    """
    Создать все необходимые ссылки для плагина
    
    Args:
        plugin_name: Имя плагина
        
    Returns:
        dict: Словарь с путями к созданным ссылкам
    """
    return {
        'addon_link': create_plugin_app_link(plugin_name),
        'cgi_link': create_cgi_app_link(plugin_name),
        'xml_link': create_plugin_xml_symlink(plugin_name),
    }


def create_processing_module_symlinks(module_name: str) -> dict:
    """
    Создать все необходимые ссылки для модуля обработки
    
    Args:
        module_name: Имя модуля
        
    Returns:
        dict: Словарь с путями к созданным ссылкам
    """
    return {
        'cli_link': create_processing_module_cli_link(module_name),
        'xml_link': create_processing_module_xml_symlink(module_name),
    }


def get_standard_paths(project_root: Union[Path, str, None] = None) -> dict:
    """
    Получить стандартные пути проекта
    
    Args:
        project_root: Корневая директория проекта
        
    Returns:
        dict: Словарь с путями проекта
    """
    if project_root is None:
        project_root = cwd_path
    else:
        project_root = Path(project_root)
    
    return {
        'cwd_path': project_root,
        'interpreter_path': project_root / "venv/bin/python3",
        'config_path': project_root / 'config.toml',
        'public_path': project_root / 'public',
        'xml_path': project_root / 'xml',
        'cgi_app_path': project_root / 'cgi.py',
        'cli_app_path': project_root / 'cli.py',
        'xml_build_path': project_root / 'xml/build.xml',
        'processing_module_cli_app_path': project_root / 'processing_module_cli.py',
        'processing_module_xml_path': project_root / 'xml/processing_module.xml',
    }


def get_mgr_paths() -> dict:
    """
    Получить пути BILLmanager
    
    Returns:
        dict: Словарь с путями BILLmanager
    """
    return {
        'mgr_path': mgr_path,
        'mgr_plugin_handlers_path': mgr_plugin_handlers_path,
        'mgr_cgi_handlers_path': mgr_cgi_handlers_path,
        'mgr_processing_module_scripts_path': mgr_processing_module_scripts_path,
        'mgr_xml_path': mgr_xml_path,
    } 