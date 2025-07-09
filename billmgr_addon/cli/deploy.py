# -*- coding: utf-8 -*-

"""
Команды деплоя плагинов на сервер
"""

import glob
import subprocess
from pathlib import Path

import click
import tomlkit

from ..utils.files import create_plugin_symlinks, get_mgr_paths, unregister_processing_module
from ..utils.xml_builder import XMLBuilder


@click.group()
def deploy():
    """Команды для деплоя плагина"""
    pass


@deploy.command()
@click.option("--plugin-name", required=True, help="Имя плагина")
@click.option("--force", is_flag=True, help="Принудительная перезапись существующих файлов")
@click.option(
    "--xml-path",
    type=click.Path(exists=True, file_okay=False, path_type=Path),
    help="Путь к папке xml (по умолчанию ./xml)",
)
@click.option(
    "--server-app-folder",
    help="Путь к папке приложения на сервере (для удаленной установки)",
)
@click.option(
    "--update-xml-cache/--no-update-xml-cache",
    default=True,
    help="Обновить XML кэш после установки",
)
@click.option(
    "--install-processing-module/--no-install-processing-module",
    default=True,
    help="Устанавливать ли processing module script (по умолчанию да, если processing_module_cli.py существует)",
)
def install(plugin_name, force, xml_path, server_app_folder, update_xml_cache, install_processing_module):
    """Установить плагин в BILLmanager"""
    try:
        click.echo(f"Установка плагина {plugin_name}...")

        if not server_app_folder and not Path("cgi.py").exists():
            raise click.ClickException("Команда должна выполняться из корня проекта плагина")

        if not server_app_folder:
            if xml_path:
                click.echo(f"Сборка XML конфигурации из {xml_path}...")
                src_path = xml_path / "src"
                build_path = xml_path / "build.xml"

                if not src_path.exists():
                    raise click.ClickException(f"Папка src не найдена в {xml_path}")
            else:
                click.echo("Сборка XML конфигурации...")
                src_path = None
                build_path = None

            builder = XMLBuilder(src_path=src_path, build_path=build_path)
            builder.build()

        click.echo("Создание ссылок...")
        links = create_plugin_symlinks(plugin_name, server_app_folder, install_processing_module)

        for link_type, link_path in links.items():
            click.echo(f"  {link_type}: {link_path}")

        if server_app_folder and update_xml_cache:
            click.echo("🔄 Обновление XML кэша...")

            meta_cache_result = subprocess.run(
                ["/usr/local/mgr5/sbin/xmlinstall", "-m", "billmgr", "--meta-cache", "--apply"],
                capture_output=True,
                text=True,
            )
            if meta_cache_result.returncode != 0:
                click.echo(
                    f"Предупреждение: ошибка обновления мета-кэша: {meta_cache_result.stderr}"
                )

            lang_cache_result = subprocess.run(
                [
                    "/usr/local/mgr5/sbin/xmlinstall",
                    "-m",
                    "billmgr",
                    "--lang-cache",
                    "ru",
                    "--base",
                    "en",
                    "--apply",
                ],
                capture_output=True,
                text=True,
            )
            if lang_cache_result.returncode != 0:
                click.echo(
                    f"Предупреждение: ошибка обновления языкового кэша: {lang_cache_result.stderr}"
                )
            else:
                click.echo("  ✅ XML кэш обновлен")

        if not server_app_folder:
            click.echo("Перезагрузка BILLmanager...")
            reload_result = subprocess.run(
                ["systemctl", "reload", "billmgr"], capture_output=True, text=True
            )
            if reload_result.returncode != 0:
                click.echo(
                    f"Предупреждение: не удалось перезагрузить BILLmanager: {reload_result.stderr}"
                )

        click.echo(f"Плагин {plugin_name} успешно установлен!")

    except Exception as e:
        raise click.ClickException(f"Ошибка установки плагина: {e}")


@deploy.command()
@click.option("--plugin-name", required=True, help="Имя плагина")
def uninstall(plugin_name):
    """Удалить плагин"""
    try:
        click.echo(f"Удаление плагина {plugin_name}...")

        mgr_paths = get_mgr_paths()

        links_to_remove = [
            mgr_paths["mgr_plugin_handlers_path"] / plugin_name,
            mgr_paths["mgr_cgi_handlers_path"] / plugin_name,
            mgr_paths["mgr_xml_path"] / f"billmgr_mod_{plugin_name}.xml",
            mgr_paths["mgr_processing_path"] / f"pm{plugin_name}",
            mgr_paths["mgr_xml_path"] / f"billmgr_mod_pm{plugin_name}.xml",
        ]

        for link_path in links_to_remove:
            if link_path.exists():
                if link_path.is_symlink():
                    link_path.unlink()
                    click.echo(f"  Удалена ссылка: {link_path}")
                else:
                    link_path.unlink()
                    click.echo(f"  Удален файл: {link_path}")

        if unregister_processing_module(plugin_name):
            click.echo(f"  Processing module pm{plugin_name} отменен")
        else:
            click.echo(f"  Предупреждение: не удалось отменить регистрацию processing module pm{plugin_name}")

        click.echo("Перезагрузка BILLmanager...")
        restart_cmd = f"/usr/local/mgr5/sbin/mgrctl -m billmgr exit"
        reload_result = subprocess.run(restart_cmd, capture_output=True, text=True)
        if reload_result.returncode != 0:
            click.echo(
                f"Предупреждение: не удалось перезагрузить BILLmanager: {reload_result.stderr}"
            )

        click.echo(f"Плагин {plugin_name} успешно удален!")

    except Exception as e:
        raise click.ClickException(f"Ошибка удаления плагина: {e}")


@deploy.command()
@click.option("--plugin-name", required=True, help="Имя плагина")
def status(plugin_name):
    """Показать статус установки плагина(для вызова на сервере)"""
    try:
        mgr_paths = get_mgr_paths()

        links_to_check = {
            "Addon handler": mgr_paths["mgr_plugin_handlers_path"] / plugin_name,
            "CGI handler": mgr_paths["mgr_cgi_handlers_path"] / plugin_name,
            "XML config": mgr_paths["mgr_xml_path"] / f"billmgr_mod_{plugin_name}.xml",
            "Processing module": mgr_paths["mgr_processing_path"] / f"pm{plugin_name}",
        }

        click.echo(f"Статус плагина {plugin_name}:")

        all_exist = True
        for name, path in links_to_check.items():
            exists = path.exists()
            status_icon = "✓" if exists else "✗"
            click.echo(f"  {status_icon} {name}: {path}")
            if not exists:
                all_exist = False

        if all_exist:
            click.echo("Плагин полностью установлен")
        else:
            click.echo("Плагин установлен не полностью")

    except Exception as e:
        raise click.ClickException(f"Ошибка проверки статуса: {e}")


@deploy.command()
@click.option(
    "--xml-path",
    type=click.Path(exists=True, file_okay=False, path_type=Path),
    help="Путь к папке xml (по умолчанию ./xml)",
)
def build_xml(xml_path):
    """Собрать XML конфигурацию"""
    try:
        if xml_path:
            click.echo(f"Сборка XML конфигурации из {xml_path}...")
        else:
            click.echo("Сборка XML конфигурации...")

        from ..utils.xml_builder import XMLBuilder

        if xml_path:
            src_path = xml_path / "src"
            build_path = xml_path / "build.xml"

            if not src_path.exists():
                raise click.ClickException(f"Папка src не найдена в {xml_path}")
        else:
            src_path = None
            build_path = None

        builder = XMLBuilder(src_path=src_path, build_path=build_path)
        output_path = builder.build()
        click.echo(f"XML конфигурация собрана: {output_path}")

    except Exception as e:
        raise click.ClickException(f"Ошибка сборки XML: {e}")


@deploy.command()
@click.option("--environment", "-e", required=True, help="Окружение деплоя (dev, prod)")
@click.option("--plugin-name", required=True, help="Имя плагина для установки на сервере")
@click.option("--config", "-c", default="deploy.toml", help="Путь к файлу конфигурации деплоя")
@click.option("--backup/--no-backup", default=True, help="Создать бэкап перед деплоем")
@click.option("--install/--no-install", default=True, help="Установить плагин после деплоя")
@click.option(
    "--restart-billmgr/--no-restart-billmgr",
    default=False,
    help="Перезапустить BILLmanager после деплоя",
)
@click.option("--dry-run", is_flag=True, help="Показать команды без выполнения")
@click.option(
    "--xml-path",
    type=click.Path(exists=True, file_okay=False, path_type=Path),
    help="Путь к папке xml (по умолчанию ./xml)",
)
@click.option(
    "--install-processing-module/--no-install-processing-module",
    default=True,
    help="Устанавливать ли processing module script (по умолчанию да, если processing_module_cli.py существует)",
)
def remote_deploy(
    environment, plugin_name, config, backup, install, restart_billmgr, dry_run, xml_path, install_processing_module
):
    """Деплой плагина на удаленный сервер"""
    try:
        click.echo(f"Удаленный деплой плагина '{plugin_name}' в окружение '{environment}'")

        if not Path("cgi.py").exists():
            raise click.ClickException("Команда должна выполняться из корня проекта плагина")

        config_path = Path(config)
        if not config_path.exists():
            raise click.ClickException(f"Файл конфигурации '{config}' не найден")

        try:
            with open(config_path, "r", encoding="utf-8") as f:
                deploy_config = tomlkit.load(f).unwrap()
        except Exception as e:
            raise click.ClickException(f"Ошибка чтения конфигурации: {e}")

        if environment not in deploy_config:
            raise click.ClickException(f"Окружение '{environment}' не найдено в конфигурации")

        env_config = deploy_config[environment]
        required_fields = ["server", "app_folder"]
        missing_fields = [field for field in required_fields if field not in env_config]
        if missing_fields:
            raise click.ClickException(
                f"Отсутствуют обязательные поля в конфигурации: {missing_fields}"
            )

        server = env_config["server"]
        app_folder = env_config["app_folder"]
        ssh_options = env_config.get("ssh_options", "-A")

        click.echo(f"Сервер: {server}")
        click.echo(f"Папка: {app_folder}")

        if dry_run:
            click.echo("Режим dry-run: команды не будут выполнены")

        click.echo("Проверка доступности сервера...")
        check_cmd = f"ssh {ssh_options} {server} 'test -d {app_folder}'"
        if dry_run:
            click.echo(f"  Команда: {check_cmd}")
        else:
            result = subprocess.run(check_cmd, shell=True, capture_output=True, text=True)
            if result.returncode != 0:
                raise click.ClickException(f"Папка {app_folder} не найдена на сервере {server}")

        if backup:
            click.echo("Создание бэкапа...")
            backup_cmd = f"""ssh {ssh_options} {server} "cd {app_folder} && \\
                tar -zcf backup.tar.gz \\
                    --exclude='venv' --exclude='*.pyc' --exclude='__pycache__' \\
                    app public xml *.py *.toml requirements.txt README.md 2>/dev/null || true" """

            if dry_run:
                click.echo(f"  Команда: {backup_cmd}")
            else:
                result = subprocess.run(backup_cmd, shell=True)
                if result.returncode == 0:
                    click.echo("Бэкап создан: backup.tar.gz")
                else:
                    click.echo("Предупреждение: ошибка создания бэкапа")

        click.echo("Очистка старых файлов...")
        cleanup_cmd = f"""ssh {ssh_options} {server} "cd {app_folder} && \\
            find app -mindepth 1 -delete 2>/dev/null || true && \\
            find public -mindepth 1 -delete 2>/dev/null || true && \\
            find xml -mindepth 1 -delete 2>/dev/null || true" """

        if dry_run:
            click.echo(f"  Команда: {cleanup_cmd}")
        else:
            subprocess.run(cleanup_cmd, shell=True)

        if xml_path:
            click.echo(f"Сборка XML конфигурации из {xml_path}...")
        else:
            click.echo("Сборка XML конфигурации...")

        if not dry_run:
            if xml_path:
                src_path = xml_path / "src"
                build_path = xml_path / "build.xml"

                if not src_path.exists():
                    raise click.ClickException(f"Папка src не найдена в {xml_path}")
            else:
                src_path = None
                build_path = None

            builder = XMLBuilder(src_path=src_path, build_path=build_path)
            builder.build()

        click.echo("Синхронизация файлов...")

        files_to_sync = []

        for dir_name in ["app", "public", "xml"]:
            if Path(dir_name).exists():
                files_to_sync.append(dir_name)

        for pattern in ["*.py", "*.toml"]:
            files_to_sync.extend(glob.glob(pattern))

        for file_name in [
            "requirements.txt",
            "README.md",
            "cgi.py",
            "settings.py",
            "build_xml.py",
            "cli.py",
            "processing_module_cli.py",
        ]:
            if Path(file_name).exists():
                files_to_sync.append(file_name)

        if not files_to_sync:
            raise click.ClickException("Нет файлов для синхронизации")

        exclude_patterns = [
            "--exclude=*.pyc",
            "--exclude=__pycache__",
            "--exclude=.git",
            "--exclude=.idea",
            "--exclude=.vscode",
            "--exclude=.mypy_cache",
            "--exclude=xml/src",
            "--exclude=venv",
        ]

        rsync_cmd = (
            ["rsync", "-rltz"] + exclude_patterns + files_to_sync + [f"{server}:{app_folder}"]
        )

        if dry_run:
            click.echo(f"  Команда: {' '.join(rsync_cmd)}")
        else:
            result = subprocess.run(rsync_cmd)
            if result.returncode != 0:
                raise click.ClickException("Ошибка синхронизации файлов")
            click.echo("  Файлы синхронизированы")

        click.echo("Создание виртуального окружения на сервере...")
        venv_cmd = f"""ssh {ssh_options} {server} "cd {app_folder} && \\
            python3.8 -m venv venv" """

        if dry_run:
            click.echo(f"  Команда: {venv_cmd}")
        else:
            result = subprocess.run(venv_cmd, shell=True)
            if result.returncode == 0:
                click.echo("  Виртуальное окружение создано")
            else:
                click.echo("  Предупреждение: ошибка создания виртуального окружения")

        click.echo("Установка зависимостей...")
        deps_cmd = f"""ssh {ssh_options} {server} "cd {app_folder} && \\
            source venv/bin/activate && \\
            pip install -r requirements.txt" """

        if dry_run:
            click.echo(f"  Команда: {deps_cmd}")
        else:
            result = subprocess.run(deps_cmd, shell=True)
            if result.returncode == 0:
                click.echo("  Зависимости установлены")
            else:
                click.echo("  Предупреждение: ошибка установки зависимостей")

        if install:
            click.echo("Установка плагина...")
            
            # Добавляем флаг processing module если он включен
            processing_module_flag = "--install-processing-module" if install_processing_module else "--no-install-processing-module"
            
            install_cmd = f"""ssh {ssh_options} {server} "cd {app_folder} && \\
                source venv/bin/activate && \\
                billmgr-addon deploy install --plugin-name {plugin_name} --server-app-folder {app_folder} {processing_module_flag}" """

            if dry_run:
                click.echo(f"  Команда: {install_cmd}")
            else:
                result = subprocess.run(install_cmd, shell=True)
                if result.returncode == 0:
                    click.echo("  Плагин установлен")
                else:
                    click.echo("  Предупреждение: ошибка установки плагина")

        if restart_billmgr or install:
            click.echo("Перезапуск BILLmanager...")
            restart_cmd = (
                f"ssh {ssh_options} {server} '/usr/local/mgr5/sbin/mgrctl -m billmgr exit'"
            )

            if dry_run:
                click.echo(f"  Команда: {restart_cmd}")
            else:
                result = subprocess.run(restart_cmd, shell=True)
                if result.returncode == 0:
                    click.echo("  BILLmanager перезапущен")
                else:
                    click.echo("  Предупреждение: ошибка перезапуска BILLmanager")

        click.echo("Деплой завершен успешно")

        if not install:
            click.echo("Для установки плагина выполните:")
            processing_module_flag = "--install-processing-module" if install_processing_module else "--no-install-processing-module"
            click.echo(
                f"   ssh {server} 'cd {app_folder} && source venv/bin/activate && sudo billmgr-addon deploy install --plugin-name {plugin_name} --server-app-folder {app_folder} {processing_module_flag}'"
            )

        if not restart_billmgr:
            click.echo("Для перезапуска BILLmanager выполните:")
            click.echo(f"   ssh {server} 'systemctl restart billmgr'")

    except Exception as e:
        raise click.ClickException(f"Ошибка удаленного деплоя: {e}")


# Экспорт
__all__ = ["deploy"]
