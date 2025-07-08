# -*- coding: utf-8 -*-

import os
from pathlib import Path

import click

from ..scaffold import ProjectScaffold
from ..utils.files import create_plugin_symlinks
from .deploy import deploy as deploy_commands


@click.group()
@click.version_option()
def main():
    """BILLmanager Addon Framework CLI"""
    pass


@main.command()
@click.option("--name", help="Имя проекта (по умолчанию: имя текущей директории)")
@click.option(
    "--path", help="Путь для создания проекта (если не указан, создается в текущей директории)"
)
@click.option("--template", default="basic", help="Шаблон проекта")
def create_project(name: str, path: str, template: str):
    """Создать новый проект плагина"""

    if name:
        project_name = name
    else:
        project_name = Path.cwd().name
        if project_name in [".", "", "/"]:
            project_name = "my-plugin"

    if path:
        project_path = Path(path) / project_name
        click.echo(f"Создание проекта '{project_name}' в '{project_path}'...")
    else:
        project_path = Path()
        click.echo(f"Создание проекта '{project_name}' в текущей директории...")

    scaffold = ProjectScaffold(project_name, project_path, template)

    try:
        scaffold.create()
        click.echo(f"Проект '{project_name}' успешно создан!")
        if path:
            click.echo(f"Путь: {project_path.absolute()}")
        else:
            click.echo(f"Путь: {project_path.absolute()}")
        click.echo()

        plugin_name_norm = project_name.lower().replace("-", "_")

        click.echo("Следующие шаги:")
        if path:
            click.echo(f"  cd {project_name}")
        click.echo("  # Настройте config.toml")
        click.echo(f"  sudo billmgr-addon deploy install --plugin-name {plugin_name_norm}")
        click.echo()
        click.echo("Для удаленного деплоя:")
        click.echo("  # Настроить deploy.toml (пример в deploy.example.toml)")
        click.echo(f"  billmgr-addon deploy remote-deploy -e dev --plugin-name {plugin_name_norm}")
    except Exception as e:
        click.echo(f"Ошибка создания проекта: {e}")
        raise click.Abort()


@main.command()
@click.option("--plugin-name", required=True, help="Имя плагина")
@click.option(
    "--install-processing-module/--no-install-processing-module",
    default=True,
    help="Устанавливать ли processing module script (по умолчанию да, если processing_module_cli.py существует)",
)
def install(plugin_name: str, install_processing_module: bool):
    """Установить плагин в BILLmanager"""
    click.echo(f"Установка плагина '{plugin_name}' в BILLmanager...")

    try:
        mgr_path = Path("/usr/local/mgr5")
        if not mgr_path.exists():
            raise click.ClickException("BILLmanager не найден в системе")

        if not os.access(mgr_path, os.W_OK):
            raise click.ClickException("Недостаточно прав для установки. Запустите с sudo.")

        links = create_plugin_symlinks(plugin_name, install_processing_module=install_processing_module)

        click.echo("Ссылки созданы:")
        for link_type, link_path in links.items():
            click.echo(f"  {link_type}: {link_path}")

        click.echo()
        click.echo("Для применения изменений выполните:")
        click.echo("  systemctl restart billmgr")

    except Exception as e:
        click.echo(f"Ошибка установки: {e}")
        raise click.Abort()


@main.command()
@click.option(
    "--xml-path",
    type=click.Path(exists=True, file_okay=False, path_type=Path),
    help="Путь к папке xml (по умолчанию ./xml)",
)
def build_xml(xml_path):
    """Собрать XML файлы плагина"""
    from ..utils.xml_builder import XMLBuilder

    if xml_path:
        click.echo(f"Сборка XML файлов из {xml_path}...")
        src_path = xml_path / "src"
        build_path = xml_path / "build.xml"

        if not src_path.exists():
            raise click.ClickException(f"Папка src не найдена в {xml_path}")
    else:
        click.echo("Сборка XML файлов...")
        src_path = None
        build_path = None

    try:
        builder = XMLBuilder(src_path=src_path, build_path=build_path)
        output_path = builder.build()
        click.echo(f"XML собран: {output_path}")
    except Exception as e:
        click.echo(f"Ошибка сборки XML: {e}")
        raise click.Abort()


main.add_command(deploy_commands)


if __name__ == "__main__":
    main()
