# -*- coding: utf-8 -*-

"""
Команды деплоя плагинов на сервер BILLmanager
"""

import os
import subprocess
from pathlib import Path

import click
import tomlkit

from ..utils.files import create_plugin_symlinks, get_mgr_paths
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
def install(plugin_name, force, xml_path, server_app_folder, update_xml_cache):
    """Установить плагин в BILLmanager"""
    try:
        click.echo(f"Установка плагина {plugin_name}...")

        # Проверяем, что мы в корне проекта (только для локальной установки)
        if not server_app_folder and not Path("cgi.py").exists():
            raise click.ClickException("Команда должна выполняться из корня проекта плагина")

        # Собираем XML (только для локальной установки)
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

        # Создаем ссылки
        click.echo("Создание ссылок...")
        links = create_plugin_symlinks(plugin_name, server_app_folder)

        for link_type, link_path in links.items():
            click.echo(f"  {link_type}: {link_path}")

        # Обновление XML кэша для серверной установки
        if server_app_folder and update_xml_cache:
            click.echo("🔄 Обновление XML кэша...")
            
            # Обновляем мета-кэш
            meta_cache_result = subprocess.run(
                ["/usr/local/mgr5/sbin/xmlinstall", "-m", "billmgr", "--meta-cache", "--apply"],
                capture_output=True, text=True
            )
            if meta_cache_result.returncode != 0:
                click.echo(f"Предупреждение: ошибка обновления мета-кэша: {meta_cache_result.stderr}")
            
            # Обновляем языковой кэш
            lang_cache_result = subprocess.run(
                ["/usr/local/mgr5/sbin/xmlinstall", "-m", "billmgr", "--lang-cache", "ru", "--base", "en", "--apply"],
                capture_output=True, text=True
            )
            if lang_cache_result.returncode != 0:
                click.echo(f"Предупреждение: ошибка обновления языкового кэша: {lang_cache_result.stderr}")
            else:
                click.echo("  ✅ XML кэш обновлен")

        # Перезагружаем BILLmanager (только если не задан server_app_folder)
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
    """Удалить плагин из BILLmanager"""
    try:
        click.echo(f"Удаление плагина {plugin_name}...")

        mgr_paths = get_mgr_paths()

        # Удаляем ссылки
        links_to_remove = [
            mgr_paths["mgr_plugin_handlers_path"] / plugin_name,
            mgr_paths["mgr_cgi_handlers_path"] / plugin_name,
            mgr_paths["mgr_xml_path"] / f"billmgr_mod_{plugin_name}.xml",
        ]

        for link_path in links_to_remove:
            if link_path.exists():
                link_path.unlink()
                click.echo(f"  Удалена ссылка: {link_path}")

        # Перезагружаем BILLmanager
        click.echo("Перезагрузка BILLmanager...")
        reload_result = subprocess.run(
            ["systemctl", "reload", "billmgr"], capture_output=True, text=True
        )
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
    """Показать статус установки плагина"""
    try:
        mgr_paths = get_mgr_paths()

        links_to_check = {
            "Addon handler": mgr_paths["mgr_plugin_handlers_path"] / plugin_name,
            "CGI handler": mgr_paths["mgr_cgi_handlers_path"] / plugin_name,
            "XML config": mgr_paths["mgr_xml_path"] / f"billmgr_mod_{plugin_name}.xml",
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

        # Используем встроенный XMLBuilder вместо внешнего скрипта
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
@click.option("--host", default="localhost", help="Хост для сервера разработки")
@click.option("--port", default=5000, help="Порт для сервера разработки")
@click.option("--debug", is_flag=True, help="Режим отладки")
def dev_server(host, port, debug):
    """Запустить сервер разработки"""
    try:
        click.echo(f"Запуск сервера разработки на {host}:{port}")

        if not Path("cgi.py").exists():
            raise click.ClickException("Файл cgi.py не найден в текущей директории")

        env = os.environ.copy()
        env["FLASK_ENV"] = "development" if debug else "production"
        env["FLASK_DEBUG"] = "1" if debug else "0"

        # Запускаем через Python с параметрами
        cmd = ["python", "cgi.py", "--dev", "--host", host, "--port", str(port)]
        if debug:
            cmd.append("--debug")

        subprocess.run(cmd, env=env)

    except KeyboardInterrupt:
        click.echo("\nСервер остановлен")
    except Exception as e:
        raise click.ClickException(f"Ошибка запуска сервера: {e}")


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
def remote_deploy(
    environment, plugin_name, config, backup, install, restart_billmgr, dry_run, xml_path
):
    """Деплой плагина на удаленный сервер"""
    try:
        click.echo(f"🚀 Удаленный деплой плагина '{plugin_name}' в окружение '{environment}'")

        # Проверяем, что мы в корне проекта
        if not Path("cgi.py").exists():
            raise click.ClickException("Команда должна выполняться из корня проекта плагина")

        # Читаем конфигурацию деплоя
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

        click.echo(f"📡 Сервер: {server}")
        click.echo(f"📁 Папка: {app_folder}")

        if dry_run:
            click.echo("🔍 Режим dry-run: команды не будут выполнены")

        # 1. Проверяем доступность сервера и папки
        click.echo("🔍 Проверка доступности сервера...")
        check_cmd = f"ssh {ssh_options} {server} 'test -d {app_folder}'"
        if dry_run:
            click.echo(f"  Команда: {check_cmd}")
        else:
            result = subprocess.run(check_cmd, shell=True, capture_output=True, text=True)
            if result.returncode != 0:
                raise click.ClickException(f"Папка {app_folder} не найдена на сервере {server}")

        # 2. Создание бэкапа
        if backup:
            click.echo("💾 Создание бэкапа...")
            timestamp = subprocess.run(
                ["date", "+%Y%m%d-%H%M%S"], capture_output=True, text=True
            ).stdout.strip()
            backup_cmd = f"""ssh {ssh_options} {server} "cd {app_folder} && \\
                tar -zcf backup-{timestamp}.tar.gz \\
                    --exclude='venv' --exclude='*.pyc' --exclude='__pycache__' \\
                    app public xml *.py *.toml requirements.txt README.md 2>/dev/null || true" """

            if dry_run:
                click.echo(f"  Команда: {backup_cmd}")
            else:
                result = subprocess.run(backup_cmd, shell=True)
                if result.returncode == 0:
                    click.echo(f"Бэкап создан: backup-{timestamp}.tar.gz")
                else:
                    click.echo("Предупреждение: ошибка создания бэкапа")

        # 3. Очистка старых файлов
        click.echo("🧹 Очистка старых файлов...")
        cleanup_cmd = f"""ssh {ssh_options} {server} "cd {app_folder} && \\
            find app -mindepth 1 -delete 2>/dev/null || true && \\
            find public -mindepth 1 -delete 2>/dev/null || true && \\
            find xml -mindepth 1 -delete 2>/dev/null || true" """

        if dry_run:
            click.echo(f"  Команда: {cleanup_cmd}")
        else:
            subprocess.run(cleanup_cmd, shell=True)

        # 4. Сборка XML локально
        if xml_path:
            click.echo(f"🔧 Сборка XML конфигурации из {xml_path}...")
        else:
            click.echo("🔧 Сборка XML конфигурации...")

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

        # 5. Синхронизация файлов
        click.echo("📦 Синхронизация файлов...")
        files_to_sync = ["app", "public", "xml", "*.py", "*.toml", "requirements.txt", "README.md"]

        # Исключения (убираем venv из exclude так как он создается на сервере)
        exclude_patterns = [
            "--exclude=*.pyc",
            "--exclude=__pycache__",
            "--exclude=.git",
            "--exclude=.idea",
            "--exclude=.vscode",
            "--exclude=.mypy_cache",
            "--exclude=xml/src",  # Исключаем исходники XML, оставляем build.xml
            "--exclude=venv",     # Исключаем venv - он создается на сервере
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
            click.echo("  ✅ Файлы синхронизированы")

        # 6. Создание виртуального окружения на сервере
        click.echo("🐍 Создание виртуального окружения на сервере...")
        venv_cmd = f"""ssh {ssh_options} {server} "cd {app_folder} && \\
            python3 -m venv venv" """

        if dry_run:
            click.echo(f"  Команда: {venv_cmd}")
        else:
            result = subprocess.run(venv_cmd, shell=True)
            if result.returncode == 0:
                click.echo("  ✅ Виртуальное окружение создано")
            else:
                click.echo("  ⚠️  Предупреждение: ошибка создания виртуального окружения")

        # 7. Установка зависимостей на сервере
        click.echo("📋 Установка зависимостей...")
        deps_cmd = f"""ssh {ssh_options} {server} "cd {app_folder} && \\
            source venv/bin/activate && \\
            pip install -r requirements.txt" """

        if dry_run:
            click.echo(f"  Команда: {deps_cmd}")
        else:
            result = subprocess.run(deps_cmd, shell=True)
            if result.returncode == 0:
                click.echo("  ✅ Зависимости установлены")
            else:
                click.echo("  ⚠️  Предупреждение: ошибка установки зависимостей")

        # 8. Установка плагина
        if install:
            click.echo("⚙️  Установка плагина...")
            install_cmd = f"""ssh {ssh_options} {server} "cd {app_folder} && \\
                source venv/bin/activate && \\
                billmgr-addon deploy install --plugin-name {plugin_name} --server-app-folder {app_folder}" """

            if dry_run:
                click.echo(f"  Команда: {install_cmd}")
            else:
                result = subprocess.run(install_cmd, shell=True)
                if result.returncode == 0:
                    click.echo("  ✅ Плагин установлен")
                else:
                    click.echo("  ⚠️  Предупреждение: ошибка установки плагина")

        # 9. Перезапуск BILLmanager
        if restart_billmgr or install:  # Перезапускаем если установили плагин или явно запрошен перезапуск
            click.echo("🔄 Перезапуск BILLmanager...")
            restart_cmd = f"ssh {ssh_options} {server} '/usr/local/mgr5/sbin/mgrctl -m billmgr exit'"

            if dry_run:
                click.echo(f"  Команда: {restart_cmd}")
            else:
                result = subprocess.run(restart_cmd, shell=True)
                if result.returncode == 0:
                    click.echo("  ✅ BILLmanager перезапущен")
                else:
                    click.echo("  ⚠️  Предупреждение: ошибка перезапуска BILLmanager")

        click.echo("🎉 Деплой завершен успешно!")

        if not install:
            click.echo("💡 Для установки плагина выполните:")
            click.echo(
                f"   ssh {server} 'cd {app_folder} && source venv/bin/activate && sudo billmgr-addon deploy install --plugin-name {plugin_name}'"
            )

        if not restart_billmgr:
            click.echo("💡 Для перезапуска BILLmanager выполните:")
            click.echo(f"   ssh {server} 'systemctl restart billmgr'")

    except Exception as e:
        raise click.ClickException(f"Ошибка удаленного деплоя: {e}")


# Экспорт
__all__ = ["deploy"]
