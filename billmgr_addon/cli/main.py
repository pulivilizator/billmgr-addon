# -*- coding: utf-8 -*-

import click
import os
import sys
from pathlib import Path

from ..scaffold import ProjectScaffold
from ..utils.files import create_plugin_symlinks, create_processing_module_symlinks
from .deploy import deploy as deploy_commands


@click.group()
@click.version_option()
def main():
    """BILLmanager Addon Framework CLI"""
    pass


@main.command()
@click.argument('project_name')
@click.option('--path', default='.', help='Путь для создания проекта')
@click.option('--template', default='basic', help='Шаблон проекта')
def create_project(project_name: str, path: str, template: str):
    """Создать новый проект плагина"""
    click.echo(f"Создание проекта '{project_name}' в '{path}'...")
    
    project_path = Path(path) / project_name
    scaffold = ProjectScaffold(project_name, project_path, template)
    
    try:
        scaffold.create()
        click.echo(f"✅ Проект '{project_name}' успешно создан!")
        click.echo(f"📁 Путь: {project_path.absolute()}")
        click.echo()
        
        plugin_name_norm = project_name.lower().replace('-', '_')

        click.echo("Следующие шаги:")
        click.echo(f"  cd {project_name}")
        click.echo("  # Настройте config.toml")
        click.echo(f"  sudo billmgr-addon deploy install --plugin-name {plugin_name_norm}")
        click.echo()
        click.echo("Для удаленного деплоя:")
        click.echo("  # Настроить deploy.toml (пример в deploy.example.toml)")
        click.echo(f"  billmgr-addon deploy remote-deploy -e dev --plugin-name {plugin_name_norm}")
    except Exception as e:
        click.echo(f"❌ Ошибка создания проекта: {e}")
        raise click.Abort()


@main.command()
@click.option('--plugin-name', required=True, help='Имя плагина')
def install(plugin_name: str):
    """Установить плагин в BILLmanager"""
    click.echo(f"Установка плагина '{plugin_name}' в BILLmanager...")
    
    try:
        # Проверяем права доступа
        mgr_path = Path("/usr/local/mgr5")
        if not mgr_path.exists():
            raise click.ClickException("BILLmanager не найден в системе")
        
        if not os.access(mgr_path, os.W_OK):
            raise click.ClickException("Недостаточно прав для установки. Запустите с sudo.")
        
        # Создаем ссылки
        links = create_plugin_symlinks(plugin_name)
        
        click.echo("✅ Ссылки созданы:")
        for link_type, link_path in links.items():
            click.echo(f"  {link_type}: {link_path}")
        
        click.echo()
        click.echo("Для применения изменений выполните:")
        click.echo("  systemctl restart billmgr")
        
    except Exception as e:
        click.echo(f"❌ Ошибка установки: {e}")
        raise click.Abort()


@main.command()
@click.option('--module-name', required=True, help='Имя модуля обработки')
def install_processing_module(module_name: str):
    """Установить модуль обработки в BILLmanager"""
    click.echo(f"Установка модуля обработки '{module_name}' в BILLmanager...")
    
    try:
        # Проверяем права доступа
        mgr_path = Path("/usr/local/mgr5")
        if not mgr_path.exists():
            raise click.ClickException("BILLmanager не найден в системе")
        
        if not os.access(mgr_path, os.W_OK):
            raise click.ClickException("Недостаточно прав для установки. Запустите с sudo.")
        
        # Создаем ссылки
        links = create_processing_module_symlinks(module_name)
        
        click.echo("✅ Ссылки созданы:")
        for link_type, link_path in links.items():
            click.echo(f"  {link_type}: {link_path}")
        
        click.echo()
        click.echo("Для применения изменений выполните:")
        click.echo("  systemctl restart billmgr")
        
    except Exception as e:
        click.echo(f"❌ Ошибка установки: {e}")
        raise click.Abort()


@main.command()
def build_xml():
    """Собрать XML файлы плагина"""
    from ..utils.xml_builder import XMLBuilder
    
    click.echo("Сборка XML файлов...")
    
    try:
        builder = XMLBuilder()
        output_path = builder.build()
        click.echo(f"✅ XML собран: {output_path}")
    except Exception as e:
        click.echo(f"❌ Ошибка сборки XML: {e}")
        raise click.Abort()


# Добавляем группу команд деплоя
main.add_command(deploy_commands)


if __name__ == '__main__':
    main() 