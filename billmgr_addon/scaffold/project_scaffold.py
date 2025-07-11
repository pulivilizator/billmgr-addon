# -*- coding: utf-8 -*-
#
import string
from pathlib import Path
from typing import Dict


class ProjectScaffold:
    """
    Генератор шаблонов проектов плагинов
    """

    def __init__(self, project_name: str, project_path: Path, template: str = "basic"):
        self.project_name = project_name
        self.project_path = Path(project_path)
        self.template = template

        self.template_vars = {
            "project_name": project_name,
            "plugin_name": project_name.lower().replace("-", "_"),
            "class_name": self._to_class_name(project_name),
        }

    def _to_class_name(self, name: str) -> str:
        return "".join(word.capitalize() for word in name.replace("-", "_").split("_"))

    def create(self) -> None:
        self._check_conflicts()

        self._create_directories()

        self._create_files()

        print(f"Проект {self.project_name} создан в {self.project_path}")

    def _check_conflicts(self) -> None:
        key_files = ["app/__init__.py", "cgi.py", "cli.py", "xml/src/main.xml"]

        existing_files = []
        for file_path in key_files:
            full_path = self.project_path / file_path
            if full_path.exists():
                existing_files.append(file_path)

        if existing_files:
            files_list = ", ".join(existing_files)
            raise ValueError(f"Проект уже существует. Найдены файлы: {files_list}")

    def _create_directories(self) -> None:
        dirs = [
            self.project_path,
            self.project_path / "app",
            self.project_path / "app" / "endpoints",
            self.project_path / "app" / "services", 
            self.project_path / "app" / "blueprints",
            self.project_path / "app" / "blueprints" / "processing_module",
            self.project_path / "app" / "blueprints" / "cli",
            self.project_path / "xml" / "src",
            self.project_path / "public",
        ]

        for dir_path in dirs:
            dir_path.mkdir(parents=True, exist_ok=True)

    def _create_files(self) -> None:
        files = self._get_template_files()

        for file_path, content in files.items():
            full_path = self.project_path / file_path
            full_path.parent.mkdir(parents=True, exist_ok=True)

            rendered_content = string.Template(content).safe_substitute(self.template_vars)

            with open(full_path, "w", encoding="utf-8") as f:
                f.write(rendered_content)

    def _get_template_files(self) -> Dict[str, str]:
        return {
            "requirements.txt": self._get_requirements_template(),
            "config.example.toml": self._get_config_template(),
            "deploy.example.toml": self._get_deploy_config_template(),
            ".gitignore": self._get_gitignore_template(),
            # Python пакет в папке app
            "app/__init__.py": self._get_main_init_template(),
            "app/app.py": self._get_app_template(),
            "app/endpoints/__init__.py": self._get_endpoints_init_template(),
            "app/endpoints/example.py": self._get_example_endpoint_template(),
            "app/services/__init__.py": "",
            "app/services/example.py": self._get_example_service_template(),
            "app/services/billmgr.py": self._get_billmgr_service_template(),
            #blueprints
            "app/blueprints/__init__.py": "",
            # Processing Module
            "app/blueprints/processing_module/__init__.py": self._get_processing_module_init_template(),
            "app/blueprints/processing_module/features.py": self._get_processing_module_features_template(),
            "processing_module_cli.py": self._get_processing_module_cli_template(),
            # CLI Blueprint
            "app/blueprints/cli/__init__.py": self._get_cli_init_template(),
            "app/blueprints/cli/commands.py": self._get_cli_commands_template(),
            # XML файлы
            "xml/src/main.xml": self._get_main_xml_template(),
            "xml/src/example_list.xml": self._get_example_list_xml_template(),
            "xml/src/processing_module.xml": self._get_processing_module_xml_template(),
            # Точки входа
            "cgi.py": self._get_cgi_template(),
            "cli.py": self._get_cli_template(),
            "build_xml.py": self._get_build_xml_template(),
        }

    def _get_requirements_template(self) -> str:
        return """git+https://github.com/pulivilizator/billmgr-addon.git#egg=billmgr-addon[mysqlclient]"""

    def _get_config_template(self) -> str:
        return """DEBUG = false
FORWARDED_SECRET = 'SECRET_FROM_BILLMGR_CONF'
BILLMGR_API_URL = 'https://localhost:1500/billmgr'
BILLMGR_API_USE_INTERFACE = ''
"""

    def _get_deploy_config_template(self) -> str:
        return """# Конфигурация удаленного деплоя
# Скопируйте этот файл в deploy.toml и настройте под ваши сервера

[dev]
server = "root@dev.example.com"
app_folder = "/opt/${plugin_name}"
public_folder = "/usr/local/mgr5/skins/userdata/${plugin_name}"
ssh_options = "-A"

[prod]
server = "deploy@production.example.com"
app_folder = "/opt/${plugin_name}"
public_folder = "/usr/local/mgr5/skins/userdata/${plugin_name}"
ssh_options = "-A -i ~/.ssh/production_key"
"""

    def _get_gitignore_template(self) -> str:
        return """# Python
__pycache__/
*.py[cod]
*$py.class
*.so
.Python
build/
develop-eggs/
dist/
downloads/
eggs/
.eggs/
lib/
lib64/
parts/
sdist/
var/
wheels/
*.egg-info/
.installed.cfg
*.egg

# Virtual environments
venv/
env/
ENV/

# IDE
.vscode/
.idea/
*.swp
*.swo

# Project specific
config.toml
deploy.toml
xml/build.xml
logs/
"""

    def _get_main_init_template(self) -> str:
        return '''# -*- coding: utf-8 -*-
"""
${project_name} - BILLmanager плагин
"""

from .endpoints import endpoints

__all__ = ['endpoints']
'''

    def _get_app_template(self) -> str:
        return '''# -*- coding: utf-8 -*-

"""
Фабрики Flask приложений для ${project_name}
"""
import traceback
import billmgr_addon
from billmgr_addon import (
    create_app as create_app_base, 
    create_cgi_app as create_cgi_app_base, 
    create_cli_app as create_cli_app_base,
    LOGGER
)
from billmgr_addon.core import create_common_app
from billmgr_addon.utils.logging import setup_logger
from .endpoints import endpoints
from .blueprints.processing_module import bp as processing_module_bp
from .blueprints.cli import bp as cli_bp

def create_cgi_app():
    """Создать CGI приложение"""
    
    logger = setup_logger(
        name=billmgr_addon.LOGGER_NAME,
        path=None,
        filename='app.log', 
        debug=False, 
        remove_default_handlers=True,
        enable_console=False
    )
    
    
    billmgr_addon.LOGGER = logger
    try:
        app = create_cgi_app_base(endpoints=endpoints)
        logger.info("CGI приложение создано успешно")
        return app
    except Exception as e:
        logger.error(f"Ошибка создания CGI приложения: {e}")
        logger.error(f"Traceback: {traceback.format_exc()}")
        raise

def create_app():
    """Создать Flask приложение"""
    return create_app_base(endpoints=endpoints)

def create_cli_app():
    """Создать CLI приложение"""
    app = create_cli_app_base()
    app.register_blueprint(cli_bp, cli_group=None)
    app.register_blueprint(processing_module_bp, cli_group="processing_module")
    return app

def create_processing_module_cli_app():
    """Создать CLI приложение для processing module"""
    
    logger = setup_logger(
        name=billmgr_addon.LOGGER_NAME,
        path=None,
        filename='app.log', 
        debug=False, 
        remove_default_handlers=True,
        enable_console=True
    )
    
    billmgr_addon.LOGGER = logger
    
    try:
        app = create_common_app()
        
        app.register_blueprint(processing_module_bp, cli_group=None)
        
        LOGGER.info("Processing module CLI приложение создано успешно")
        return app
    except Exception as e:
        LOGGER.error(f"Ошибка создания processing module CLI приложения: {e}")
        LOGGER.error(f"Traceback: {traceback.format_exc()}")
        raise

'''

    def _get_endpoints_init_template(self) -> str:
        return """# -*- coding: utf-8 -*-

from .example import ExampleList

# Список всех эндпоинтов плагина
endpoints = [
    ExampleList("example.list"),
]
"""

    def _get_example_endpoint_template(self) -> str:
        return '''# -*- coding: utf-8 -*-

from billmgr_addon import LOGGER, ListEndpoint, MgrList, MgrRequest


class ExampleList(ListEndpoint):
    """Пример списка"""
    auth_level = 16
    
    async def get(self, mgr_list: MgrList, mgr_request: MgrRequest):
        """Получить данные для списка"""
        LOGGER.info("ExampleList.get() started")
        sample_data = [
            {"id": 1, "name": "Элемент 1", "status": "active"},
            {"id": 2, "name": "Элемент 2", "status": "inactive"},
        ]
                
        mgr_list.set_data_rows(sample_data)
        LOGGER.info("ExampleList.get() completed")
        return mgr_list
'''

    def _get_example_service_template(self) -> str:
        return '''# -*- coding: utf-8 -*-

from typing import List, Dict, Any


async def get_items() -> List[Dict[str, Any]]:
    """Получить список элементов"""
    return [
            {"id": 1, "name": "Элемент 1", "status": "active"},
            {"id": 2, "name": "Элемент 2", "status": "inactive"},
        ]

'''

    def _get_main_xml_template(self) -> str:
        return """<?xml version="1.0" encoding="UTF-8"?>
<mgrdata>
    <handler name="${plugin_name}" type="xml">
        <func name="example.list" />
    </handler>

    <mainmenu level="user">
        <node name="${plugin_name}" image="stat" icon="m-stat" spritesvg="yes" after="customer">
            <node name="example.list" action="example.list" type="list"/>
        </node>
    </mainmenu>

    <import path="example_list.xml"/>
    <import path="processing_module.xml"/>

    <lang name="ru">
        <messages name="desktop">
            <msg name="menu_${plugin_name}">Пример плагина</msg>
            <msg name="menu_example.list">Пример списка</msg>
        </messages>
    </lang>
    <lang name="en">
        <messages name="desktop">
            <msg name="menu_${plugin_name}">Example Plugin</msg>
            <msg name="menu_example.list">Example List</msg>
        </messages>
    </lang>
</mgrdata>

"""

    def _get_example_list_xml_template(self) -> str:
        return """<?xml version="1.0" encoding="UTF-8"?>
<mgrdata>
    <metadata name="example.list" type="list" key="id" keyname="name" mgr="billmgr" level="user">
        <toolbar>
            <toolgrp name="new_group">
                <toolbtn func="example.new" name="new" img="t-new" type="new" level="user" sprite="yes" />
            </toolgrp>
            <toolgrp name="new_group_sep" separator="yes"/>
        </toolbar>
        <coldata>
            <col name="id" type="data" hidden="yes" />
            <col name="name" type="data" />
            <col name="status" type="msg" />
        </coldata>
    </metadata>

    <lang name="ru">
        <messages name="example.list">
            <msg name="title">Примеры</msg>
            <msg name="name">Название</msg>
            <msg name="status">Статус</msg>
            <msg name="active">Активен</msg>
            <msg name="inactive">Неактивен</msg>
        </messages>
    </lang>
    <lang name="en">
        <messages name="example.list">
            <msg name="title">Examples</msg>
            <msg name="name">Name</msg>
            <msg name="status">Status</msg>
            <msg name="active">Active</msg>
            <msg name="inactive">Inactive</msg>
        </messages>
    </lang>
</mgrdata>
"""

    def _get_cgi_template(self) -> str:
        return '''#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
CGI интерфейс для ${project_name}
"""

import os
import sys
from pathlib import Path

project_dir = Path(__file__).parent.resolve()

os.chdir(project_dir)

sys.path.insert(0, str(project_dir))

if 'BILLMGR_ADDON_PROJECT_ROOT' not in os.environ:
    os.environ['BILLMGR_ADDON_PROJECT_ROOT'] = str(project_dir)


from app.app import create_cgi_app
from billmgr_addon.cgi import run_with_cgi

def main():
    """Главная функция CGI скрипта"""
    app = create_cgi_app()
    run_with_cgi(app)

if __name__ == '__main__':
    main()

'''

    def _get_cli_template(self) -> str:
        return '''#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
CLI интерфейс для ${project_name}
"""

import sys
from pathlib import Path

# Добавляем текущую директорию в Python path
sys.path.insert(0, str(Path(__file__).parent))

# Импортируем приложение из папки app
from app.app import create_cli_app

if __name__ == "__main__":
    app = create_cli_app()
    # Запускаем CLI приложение
    with app.app_context():
        from billmgr_addon.cli import main
        main()
'''

    def _get_build_xml_template(self) -> str:
        return '''#!/usr/bin/env python
# -*- coding: utf-8 -*-

import billmgr_addon

if __name__ == "__main__":
    billmgr_addon.build_xml.main()
'''

    def _get_processing_module_init_template(self) -> str:
        return '''# -*- coding: utf-8 -*-

from flask import Blueprint
import click
from billmgr_addon import LOGGER, MgrErrorResponse
from .features import features_command, open_command, resume_command, suspend_command, close_command, start_command, stop_command, stat_command


bp = Blueprint("processing_module", __name__)

@bp.cli.command("execute")
@click.option("--command", type=str, required=True)
@click.option("--subcommand", type=str)
@click.option("--id", "pricelist_id", type=int)
@click.option("--item", "item_id", type=int)
@click.option("--module", "module_id", type=int)
@click.option("--param", type=str)
@click.option("--value")
@click.option("--runningoperation")
@click.option("--level")
@click.option("--userid", "user_id")
def execute(
    command,
    subcommand,
    pricelist_id,
    item_id,
    module_id,
    param,
    value,
    runningoperation,
    level,
    user_id,
):
    """Выполнить команду processing module"""
    commands = {
        "features": features_command,
        "open": open_command,
        "resume": resume_command,
        "suspend": suspend_command,
        "close": close_command,
        "start": start_command,
        "stop": stop_command,
        "stat": stat_command,
    }
    
    LOGGER.info(f"Executing processing module command: {command}")
    LOGGER.debug(f"Command parameters: item_id={item_id}, runningoperation={runningoperation}")
    
    command_handler = commands.get(command)
    if command_handler is None:
        LOGGER.error(f"Unknown command: {command}")
        raise click.UsageError(f"Option --command has invalid value '{command}'")

    ctx = click.get_current_context()
    try:
        response = command_handler(**ctx.params)
        LOGGER.info(f"Command {command} executed successfully")
        click.echo(response)
    except Exception as e:
        LOGGER.exception(f"Error executing command {command}: {e}")
        click.echo(MgrErrorResponse("Unknown processing module error")) 
        
'''

    def _get_processing_module_features_template(self) -> str:
        return '''# -*- coding: utf-8 -*-

import xml.etree.ElementTree as ET
from billmgr_addon import MgrResponse, ProcessingModuleResponse, LOGGER


class FeaturesResponse(MgrResponse):
    """Ответ на команду features"""
    
    def __init__(self) -> None:
        super().__init__()
        
        itemtypes = [{"name": "${plugin_name}"}]
        
        features = [
            {"name": "features"},
            {"name": "open"},
            {"name": "suspend"},
            {"name": "resume"},
            {"name": "close"},
            {"name": "stat"},
        ]
        
        params = [
            {"name": "api_url"},
            {"name": "api_token", "crypted": "yes"},
        ]
        
        itemtypes_element = ET.SubElement(self.root, "itemtypes")
        for itemtype_attributes in itemtypes:
            ET.SubElement(itemtypes_element, "itemtype", attrib=itemtype_attributes)

        features_element = ET.SubElement(self.root, "features")
        for feature_attributes in features:
            ET.SubElement(features_element, "feature", attrib=feature_attributes)

        params_element = ET.SubElement(self.root, "params")
        for param_attributes in params:
            ET.SubElement(params_element, "param", attrib=param_attributes)


def features_command(**kwargs):
    """Команда features - возвращает список поддерживаемых типов услуг, команд и параметров"""
    LOGGER.info("Processing features command")
    return FeaturesResponse()


def open_command(item_id=None, runningoperation=None, **kwargs):
    """Команда open - активация услуги"""
    LOGGER.info(f"Opening service {item_id} for project ${project_name}")
    
    try:
        from app.services.billmgr import get_${plugin_name}_api_credentials
        api_url, api_token = get_${plugin_name}_api_credentials()
        
        LOGGER.info(f"API settings: url={api_url}, token={'***' if api_token else 'None'}")
        
        if not api_url:
            raise ValueError("API URL is required but not provided")
        
        LOGGER.info(f"Service {item_id} opened successfully using API {api_url}")
        return ProcessingModuleResponse("ok")
        
    except Exception as e:
        LOGGER.exception(f"Error opening service {item_id}: {e}")
        return ProcessingModuleResponse("error")


def suspend_command(item_id=None, runningoperation=None, **kwargs):
    """Команда suspend - приостановка услуги"""
    LOGGER.info(f"Suspending service {item_id} for project ${project_name}")
    
    try:
        LOGGER.info(f"Service {item_id} suspended successfully")
        return ProcessingModuleResponse("ok")
        
    except Exception as e:
        LOGGER.exception(f"Error suspending service {item_id}: {e}")
        return ProcessingModuleResponse("error")


def resume_command(item_id=None, runningoperation=None, **kwargs):
    """Команда resume - возобновление услуги"""
    LOGGER.info(f"Resuming service {item_id} for project ${project_name}")
    
    try:
        LOGGER.info(f"Service {item_id} resumed successfully")
        return ProcessingModuleResponse("ok")
        
    except Exception as e:
        LOGGER.exception(f"Error resuming service {item_id}: {e}")
        return ProcessingModuleResponse("error")


def close_command(item_id=None, runningoperation=None, **kwargs):
    """Команда close - закрытие услуги"""
    LOGGER.info(f"Closing service {item_id} for project ${project_name}")
    
    try:
        LOGGER.info(f"Service {item_id} closed successfully")
        return ProcessingModuleResponse("ok")
        
    except Exception as e:
        LOGGER.exception(f"Error closing service {item_id}: {e}")
        return ProcessingModuleResponse("error")


def start_command(item_id=None, runningoperation=None, **kwargs):
    """Команда start - запуск услуги"""
    LOGGER.info(f"Starting service {item_id} for project ${project_name}")
    
    try:
        LOGGER.info(f"Service {item_id} started successfully")
        return ProcessingModuleResponse("ok")
        
    except Exception as e:
        LOGGER.exception(f"Error starting service {item_id}: {e}")
        return ProcessingModuleResponse("error")


def stop_command(item_id=None, runningoperation=None, **kwargs):
    """Команда stop - остановка услуги"""
    LOGGER.info(f"Stopping service {item_id} for project ${project_name}")
    
    try:
        LOGGER.info(f"Service {item_id} stopped successfully")
        return ProcessingModuleResponse("ok")
        
    except Exception as e:
        LOGGER.exception(f"Error stopping service {item_id}: {e}")
        return ProcessingModuleResponse("error")


def stat_command(module_id=None, **kwargs):
    """Команда stat - сбор статистики"""
    LOGGER.info(f"Collecting stats for module {module_id} in project ${project_name}")
    
    try:
        LOGGER.info(f"Stats collected successfully for module {module_id}")
        return ProcessingModuleResponse("ok")
        
    except Exception as e:
        LOGGER.exception(f"Error collecting stats for module {module_id}: {e}")
        return ProcessingModuleResponse("error")
'''

    def _get_processing_module_cli_template(self) -> str:
        return '''#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
CLI точка входа для Processing Module
Этот файл вызывается BILLmanager при обработке событий услуг
"""

from app.app import create_processing_module_cli_app

if __name__ == "__main__":
    app = create_processing_module_cli_app()
    with app.app_context():
        app.cli.commands['execute']()
'''

    def _get_processing_module_xml_template(self) -> str:
        return '''<?xml version='1.0' encoding="UTF-8"?>
<mgrdata>
    <plugin name="pm${plugin_name}">
        <group>processing_module</group>
        <author>${project_name} Team</author>
        <params>
            <type name="${plugin_name}"/>
        </params>
        <msg name="desc_short" lang="ru">${project_name}</msg>
        <msg name="desc_short" lang="en">${project_name}</msg>
        <msg name="desc_full" lang="ru">Модуль обработки для ${project_name}</msg>
        <msg name="desc_full" lang="en">Processing module for ${project_name}</msg>
    </plugin>
    
    <metadata name="processing.edit.pm${plugin_name}" type="form">
        <form title="name">
            <page name="connect">
                <field name="api_url">
                    <input type="text" name="api_url" check="url" required="no" maxlength="256"/>
                </field>
                <field name="api_token">
                    <input type="text" name="api_token" required="no" maxlength="256"/>
                </field>
            </page>
        </form>
    </metadata>
    
    <lang name="ru">
        <messages name="processing.edit.pm${plugin_name}">
            <msg name="api_url">URL API</msg>
            <msg name="api_token">Токен API</msg>
        </messages>
        <messages name="label_processing_modules">
            <msg name="pm${plugin_name}">${project_name}</msg>
            <msg name="module_pm${plugin_name}">${project_name}</msg>
        </messages>
    </lang>
    
    <lang name="en">
        <messages name="processing.edit.pm${plugin_name}">
            <msg name="api_url">API URL</msg>
            <msg name="api_token">API Token</msg>
        </messages>
        <messages name="label_processing_modules">
            <msg name="pm${plugin_name}">${project_name}</msg>
            <msg name="module_pm${plugin_name}">${project_name}</msg>
        </messages>
    </lang>
</mgrdata>
'''

    def _get_billmgr_service_template(self) -> str:
        return '''# -*- coding: utf-8 -*-

from billmgr_addon import get_db, LOGGER
from flask import current_app
import base64
from Crypto.Cipher import PKCS1_v1_5


def get_${plugin_name}_api_credentials() -> tuple:
    """Получает настройки API для processing module pm${plugin_name} из БД BILLmanager"""
    db = get_db('billmgr')

    # Получаем api_url из processingparam
    api_url_result = db.select_query(
        """
            SELECT pp.*
            FROM processingparam pp
            JOIN processingmodule pm
                ON pm.id = pp.processingmodule
                AND pm.module = 'pm${plugin_name}'
            WHERE pp.intname = 'api_url'
        """).one_or_none()

    api_url = api_url_result['value'] if api_url_result else None

    # Получаем api_token из processingcryptedparam
    api_token_result = db.select_query(
        """
            SELECT pp.*
            FROM processingcryptedparam pp
            JOIN processingmodule pm
                ON pm.id = pp.processingmodule
                AND pm.module = 'pm${plugin_name}'
            WHERE pp.intname = 'api_token'
        """).one_or_none()

    api_token_encrypted = api_token_result['value'] if api_token_result else None
    api_token = None

    if api_token_encrypted:
        try:
            api_token = decrypt_value(api_token_encrypted)
        except Exception as e:
            LOGGER.error(f"Failed to decrypt api_token: {e}")
            api_token = None

    LOGGER.info(f"Loaded API credentials: url={api_url}, token={'***' if api_token else 'None'}")
    return api_url, api_token


def decrypt_value(encrypted_value: str) -> str:
    """Расшифровать значение, зашифрованное BILLmanager"""
    encryption_key = current_app.mgr_encryption_key
    try:
        cipher = PKCS1_v1_5.new(encryption_key)
        encrypt_byte = base64.b64decode(encrypted_value.encode())
        decrypt_byte = cipher.decrypt(encrypt_byte, b'failure')
        value = decrypt_byte.decode()
    except ValueError as e:
        LOGGER.error(f"Failed to decrypt the value: {e}", exc_info=e)
        raise e
    else:
        return value


def encrypt_value(value: str) -> str:
    """Зашифровать значение для BILLmanager"""
    encryption_key = current_app.mgr_encryption_key
    try:
        cipher = PKCS1_v1_5.new(encryption_key)
        decrypt_byte = value.encode()
        encrypt_byte = cipher.encrypt(decrypt_byte)
        encrypted_value = (base64.b64encode(encrypt_byte)).decode()
    except ValueError as e:
        LOGGER.error(f"Failed to encrypt the value: {e}", exc_info=e)
        raise e
    else:
        return encrypted_value
'''

    def _get_cli_init_template(self) -> str:
        return '''# -*- coding: utf-8 -*-

from flask import Blueprint
import click
from billmgr_addon import LOGGER, get_db, mgrctl_exec
from .commands import restart_panel_command, test_command

bp = Blueprint("cli", __name__)

@bp.cli.command("test")
def test():
    """Тестовая команда для проверки работы CLI"""
    test_command()

@bp.cli.command("restart_panel")
def restart_panel():
    """Перезапустить панель BILLmanager"""
    restart_panel_command()
'''

    def _get_cli_commands_template(self) -> str:
        return '''# -*- coding: utf-8 -*-

import click
from billmgr_addon import LOGGER, get_db, mgrctl_exec
from pathlib import Path


def test_command():
    """Тестовая команда для проверки работы CLI"""
    click.echo("test started")
    
    try:
        db = get_db("billmgr")
        row = db.select_query(
            """
            SELECT 'testaddon_test' AS test_value
            """
        ).one_or_none()
        click.echo(f"Database test result: {row}")
        
        cwd_path = Path.cwd()
        click.echo(f"Project path: {cwd_path}")
        click.echo(f"Config file: {cwd_path / 'config.toml'}")
        
        LOGGER.info("Test command executed successfully")
        click.echo("test finished")
        
    except Exception as e:
        LOGGER.error(f"Test command failed: {e}")
        click.echo(f"test failed: {e}")
        raise


def restart_panel_command():
    """Перезапустить панель BILLmanager"""
    click.echo("Restarting BILLmanager panel...")
    
    try:
        mgrctl_exec(["-R"])
        LOGGER.info("Panel restart command executed successfully")
        click.echo("Панель BILLmanager перезапущена")
        
    except Exception as e:
        LOGGER.error(f"Failed to restart panel: {e}")
        click.echo(f"restart_panel failed: {e}")
        raise
'''
