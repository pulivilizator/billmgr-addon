# -*- coding: utf-8 -*-

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
            self.project_path / "app" / "i18n",
            self.project_path / "app" / "i18n" / "locales",
            self.project_path / "app" / "i18n" / "locales" / "en",
            self.project_path / "app" / "i18n" / "locales" / "en" / "LC_MESSAGES",
            self.project_path / "app" / "i18n" / "locales" / "ru",
            self.project_path / "app" / "i18n" / "locales" / "ru" / "LC_MESSAGES",
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
            "app/blueprints/cli/installation.py": self._get_cli_installation_template(),
            # i18n
            "app/i18n/__init__.py": "",
            "app/i18n/base_enum.py": self._get_i18n_base_enum_template(),
            "app/i18n/factory.py": self._get_i18n_factory_template(),
            "app/i18n/i18n.py": self._get_i18n_script_template(),
            "app/i18n/i18n_stub_script.sh": self._get_i18n_stub_script_template(),
            "app/i18n/stub.pyi": self._get_i18n_stub_template(),
            "app/i18n/locales/en/LC_MESSAGES/txt.ftl": self._get_i18n_en_locale_template(),
            "app/i18n/locales/ru/LC_MESSAGES/txt.ftl": self._get_i18n_ru_locale_template(),
            # XML файлы
            "xml/src/main.xml": self._get_main_xml_template(),
            "xml/src/example_list.xml": self._get_example_list_xml_template(),
            "xml/src/processing_module.xml": self._get_processing_module_xml_template(),
            # Точки входа
            "cgi.py": self._get_cgi_template(),
            "cli.py": self._get_cli_template(),
            "build_xml.py": self._get_build_xml_template(),
            # README
            "README.md": self._get_readme_template(),
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
    create_processing_module_cli_app as create_processing_module_cli_app_base,
    LOGGER
)
from billmgr_addon.core.i18n import register_i18n_for_app
from billmgr_addon.utils.logging import setup_logger
from .endpoints import endpoints
from .blueprints.processing_module import bp as processing_module_bp
from .blueprints.cli import bp as cli_bp
from .i18n.factory import i18n_factory

@register_i18n_for_app(i18n_factory)
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

@register_i18n_for_app(i18n_factory)
def create_cli_app():
    """Создать CLI приложение"""
    app = create_cli_app_base()
    app.register_blueprint(cli_bp, cli_group=None)
    app.register_blueprint(processing_module_bp, cli_group="processing_module")
    return app

@register_i18n_for_app(i18n_factory)
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
        app = create_processing_module_cli_app_base(processing_module_bp, cli_group=None)
        return app
    except Exception as e:
        logger.error(f"Ошибка создания processing module CLI приложения: {e}")
        logger.error(f"Traceback: {traceback.format_exc()}")
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

from typing import TYPE_CHECKING
from billmgr_addon import LOGGER, ListEndpoint, MgrList, MgrRequest
from billmgr_addon.core.i18n import TranslatorRunner

if TYPE_CHECKING:
    from app.i18n.stub import TranslatorRunner

class ExampleList(ListEndpoint):
    """Пример списка"""
    auth_level = 16
    
    async def get(self, mgr_list: MgrList, mgr_request: MgrRequest):
        """Получить данные для списка"""
        LOGGER.info("ExampleList.get() started")
        i18n: TranslatorRunner = mgr_request.i18n
        
        sample_data = [
            {"id": 1, "name": "{} 1".format(i18n.test.name()), "status": "active"},
            {"id": 2, "name": "{} 2".format(i18n.test.name()), "status": "inactive"},
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


sys.path.insert(0, str(Path(__file__).parent))

from app.app import create_cli_app

if __name__ == "__main__":
    app = create_cli_app()
    with app.app_context():
        app.cli.main()

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
from .installation import (
    install_all, 
    install_plugin,
    install_processing_module, 
    check_installation, 
    uninstall_plugin
)

bp = Blueprint("cli", __name__)

@bp.cli.command("test")
def test():
    """Тестовая команда для проверки работы CLI"""
    test_command()

@bp.cli.command("restart_panel")
def restart_panel():
    """Перезапустить панель BILLmanager"""
    restart_panel_command()

@bp.cli.command("install")
def install():
    """Полная установка плагина"""
    install_all()

@bp.cli.command("install_plugin")
def install_plugin_cmd():
    """Установка только плагина (без processing module)"""
    install_plugin()

@bp.cli.command("install_processing_module")
def install_processing_module_cmd():
    """Установка только processing module"""
    install_processing_module()

@bp.cli.command("check")
def check():
    """Проверка состояния установки"""
    check_installation()

@bp.cli.command("uninstall")
def uninstall():
    """Удаление плагина"""
    uninstall_plugin()
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
            SELECT 'test' AS test_value
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

    def _get_cli_installation_template(self) -> str:
        return '''# -*- coding: utf-8 -*-

import click
import json
import secrets
import string
from pathlib import Path
from tomlkit.toml_file import TOMLFile
from collections import namedtuple
from typing import List
from billmgr_addon import LOGGER, get_db, mgrctl_exec
from billmgr_addon.utils.files import (
    create_plugin_app_link, 
    create_cgi_app_link, 
    create_plugin_xml_symlink,
    config_path, 
    cwd_path
)

EnumerationItem = namedtuple("EnumerationItem", ["intname", "name", "name_ru"])

PLUGIN_NAME = "${project_name}"
MODULE_NAME = f"pm{PLUGIN_NAME}"


def install_all():
    click.echo("=== Полная установка плагина ===")
    _setup_billmgr_api_url()
    _setup_forwarded_secret()
    _create_plugin_symlinks()
    _create_processing_module_symlinks()
    _create_itemtype()
    _create_processingmodule()
    _restart_panel()
    _create_enumerations()
    _create_pricelist()
    _edit_prices()
    _activate_pricelist()
    click.echo("=== Установка завершена ===")


def install_plugin():
    click.echo("=== Установка плагина ===")
    _setup_billmgr_api_url()
    _setup_forwarded_secret()
    _create_plugin_symlinks()
    _restart_panel()
    click.echo("=== Установка плагина завершена ===")


def install_processing_module():
    click.echo("=== Установка Processing Module ===")
    _create_processing_module_symlinks()
    _create_itemtype()
    _create_processingmodule()
    _restart_panel()
    _create_enumerations()
    _create_pricelist()
    click.echo("=== Установка Processing Module завершена ===")


def _get_billmgr_param_value(name):
    try:
        paramlist_response = mgrctl_exec(
            [
                "paramlist",
                f"elid={name}",
                "out=json",
            ],
            capture_output=True
        )
        
        if paramlist_response is None:
            return None
            
        if isinstance(paramlist_response, bytes):
            paramlist_response = paramlist_response.decode('utf-8')
        
        paramlist_data = json.loads(paramlist_response)
        param_elem = paramlist_data["doc"]["elem"][0][name]
        value = param_elem.get("$")
        return value
    except Exception as e:
        LOGGER.error(f"Ошибка получения параметра {name}: {e}")
        return None


def _set_billmgr_param_value(name, value):
    try:
        mgrctl_exec(
            [
                "paramlist.edit",
                f"elid={name}",
                f"value={value}",
                "sok=ok",
            ]
        )
        click.echo(f"Параметр {name} установлен в конфигурации BILLmanager")
    except Exception as e:
        LOGGER.error(f"Ошибка установки параметра {name}: {e}")
        click.echo(f"Ошибка установки параметра {name}: {e}")


def _setup_forwarded_secret():
    click.echo("Настройка ForwardedSecret...")
    
    try:
        forwarded_secret = _get_billmgr_param_value("ForwardedSecret")
        
        if forwarded_secret is None or forwarded_secret == "":
            click.echo("Параметр 'ForwardedSecret' не установлен в конфигурации BILLmanager")
            click.echo("Он необходим для безопасного взаимодействия плагина с BILLmanager")
            
            forwarded_secret_length = 32
            random_forwarded_secret = ''.join(
                secrets.choice(string.ascii_letters + string.digits) 
                for _ in range(forwarded_secret_length)
            )
            
            app_config_file = TOMLFile(config_path)
            app_config = app_config_file.read()
            config_forwarded_secret = app_config.get("FORWARDED_SECRET", "")
            
            options = [
                {"id": 1, "name": f"Использовать случайно сгенерированный: '{random_forwarded_secret}'"},
                {"id": 2, "name": f"Использовать значение из config.toml: '{config_forwarded_secret}'"},
                {"id": 3, "name": "Ввести свое значение"},
                {"id": 4, "name": "Пропустить настройку"}
            ]
            
            click.echo("Выберите вариант:")
            for option in options:
                click.echo(f"  {option['id']}. {option['name']}")
            
            choice = click.prompt("Ваш выбор", type=click.IntRange(1, 4), default=1)
            
            if choice == 1:
                forwarded_secret = random_forwarded_secret
            elif choice == 2:
                forwarded_secret = config_forwarded_secret
            elif choice == 3:
                forwarded_secret = click.prompt("Введите ForwardedSecret", default="")
            else:
                click.echo("Настройка ForwardedSecret пропущена")
                return
            
            if forwarded_secret:
                _set_billmgr_param_value("ForwardedSecret", forwarded_secret)
                
                app_config["FORWARDED_SECRET"] = forwarded_secret
                app_config_file.write(app_config)
                click.echo("ForwardedSecret сохранен в config.toml")
        else:
            click.echo(f"ForwardedSecret уже настроен: {'*' * 8}")
            
    except Exception as e:
        LOGGER.error(f"Ошибка настройки ForwardedSecret: {e}")
        click.echo(f"Ошибка настройки ForwardedSecret: {e}")


def _setup_billmgr_api_url():
    click.echo("Настройка URL API BILLmanager...")
    
    try:
        server_name = _get_billmgr_param_value("ServerNameParam")
        if server_name:
            billmgr_api_url = f"https://{server_name}/billmgr"
            
            app_config_file = TOMLFile(config_path)
            app_config = app_config_file.read()
            app_config["BILLMGR_API_URL"] = billmgr_api_url
            app_config_file.write(app_config)
            
            click.echo(f"BILLMGR_API_URL установлен: {billmgr_api_url}")
        else:
            click.echo("Не удалось получить ServerNameParam, настройте BILLMGR_API_URL вручную")
            
    except Exception as e:
        LOGGER.error(f"Ошибка настройки BILLMGR_API_URL: {e}")
        click.echo(f"Ошибка настройки BILLMGR_API_URL: {e}")


def _create_plugin_symlinks():
    click.echo("Создание символических ссылок...")
    
    try:
        plugin_name = cwd_path.name
        
        plugin_app_link = create_plugin_app_link(plugin_name)
        click.echo(f"Создана ссылка на обработчик плагина: {plugin_app_link}")
        
        cgi_app_link = create_cgi_app_link(plugin_name)
        click.echo(f"Создана ссылка на CGI обработчик: {cgi_app_link}")
        
        plugin_xml_symlink = create_plugin_xml_symlink(plugin_name)
        click.echo(f"Создана ссылка на XML конфигурацию: {plugin_xml_symlink}")
        
    except Exception as e:
        LOGGER.error(f"Ошибка создания символических ссылок: {e}")
        click.echo(f"Ошибка создания символических ссылок: {e}")


def _restart_panel():
    click.echo("Перезапуск панели BILLmanager...")
    
    if click.confirm("Перезапустить панель BILLmanager? (необходимо для применения изменений)"):
        try:
            mgrctl_exec(["-R"])
            click.echo("Панель BILLmanager перезапущена")
        except Exception as e:
            LOGGER.error(f"Ошибка перезапуска панели: {e}")
            click.echo(f"Ошибка перезапуска панели: {e}")
    else:
        click.echo("Перезапуск панели пропущен")
        click.echo("ВНИМАНИЕ: Перезапустите панель вручную для применения изменений!")


def check_installation():
    click.echo("=== Проверка установки ===")
    
    try:
        app_config_file = TOMLFile(config_path)
        app_config = app_config_file.read()
        
        click.echo("Конфигурация плагина:")
        click.echo(f"  BILLMGR_API_URL: {app_config.get('BILLMGR_API_URL', 'НЕ УСТАНОВЛЕН')}")
        click.echo(f"  FORWARDED_SECRET: {'УСТАНОВЛЕН' if app_config.get('FORWARDED_SECRET') else 'НЕ УСТАНОВЛЕН'}")
        
        try:
            db = get_db("billmgr")
            row = db.select_query("SELECT 'connection_test' AS test").one_or_none()
            click.echo(f"  Подключение к БД: ОК ({row['test']})")
        except Exception as e:
            click.echo(f"  Подключение к БД: ОШИБКА ({e})")
        
        plugin_name = cwd_path.name
        files_to_check = [
            cwd_path / "cgi.py",
            cwd_path / "cli.py", 
            cwd_path / "xml" / "build.xml",
            Path(f"/usr/local/mgr5/addon/{plugin_name}"),
            Path(f"/usr/local/mgr5/etc/xml/{plugin_name}.xml"),
        ]
        
        click.echo("Файлы и ссылки:")
        for file_path in files_to_check:
            status = "ОК" if file_path.exists() else "ОТСУТСТВУЕТ"
            click.echo(f"  {file_path}: {status}")
            
    except Exception as e:
        LOGGER.error(f"Ошибка проверки установки: {e}")
        click.echo(f"Ошибка проверки установки: {e}")


def uninstall_plugin():
    click.echo("=== Удаление плагина ===")
    
    if not click.confirm("Вы уверены, что хотите удалить плагин?"):
        click.echo("Удаление отменено")
        return
    
    try:
        plugin_name = cwd_path.name
        
        links_to_remove = [
            Path(f"/usr/local/mgr5/addon/{plugin_name}"),
            Path(f"/usr/local/mgr5/etc/xml/{plugin_name}.xml"),
        ]
        
        for link_path in links_to_remove:
            if link_path.exists():
                link_path.unlink()
                click.echo(f"Удалена ссылка: {link_path}")
        
        click.echo("Плагин удален")
        click.echo("Рекомендуется перезапустить панель BILLmanager")
        
    except Exception as e:
        LOGGER.error(f"Ошибка удаления плагина: {e}")
        click.echo(f"Ошибка удаления плагина: {e}") 


def _create_processing_module_symlinks():
    click.echo("Создание символических ссылок processing module...")
    
    try:
        processing_module_cli_link = Path(f"/usr/local/mgr5/addon/{MODULE_NAME}")
        if not processing_module_cli_link.exists():
            processing_module_cli_link.symlink_to(cwd_path / "processing_module_cli.py")
            click.echo(f"Создана ссылка на processing module CLI: {processing_module_cli_link}")
        
        processing_module_xml_link = Path(f"/usr/local/mgr5/etc/xml/{MODULE_NAME}.xml")
        if not processing_module_xml_link.exists():
            processing_module_xml_link.symlink_to(cwd_path / "xml" / "build.xml")
            click.echo(f"Создана ссылка на processing module XML: {processing_module_xml_link}")
            
    except Exception as e:
        LOGGER.error(f"Ошибка создания символических ссылок processing module: {e}")
        click.echo(f"Ошибка создания символических ссылок processing module: {e}")


def _get_processingmodule():
    try:
        db = get_db("billmgr")
        processingmodule = db.select_query(
            """
            SELECT *
            FROM processingmodule
            WHERE module = %(module)s
            """,
            {"module": MODULE_NAME}
        ).one_or_none()
        return processingmodule
    except Exception as e:
        LOGGER.error(f"Ошибка получения processing module: {e}")
        return None


def _get_itemtype():
    try:
        db = get_db("billmgr")
        itemtype = db.select_query(
            """
            SELECT it.*
            FROM itemtype it
            WHERE it.intname = %(intname)s
            """,
            {"intname": PLUGIN_NAME}
        ).one_or_none()
        return itemtype
    except Exception as e:
        LOGGER.error(f"Ошибка получения itemtype: {e}")
        return None


def _get_pricelist():
    try:
        db = get_db("billmgr")
        pricelist = db.select_query(
            """
            SELECT pl.*
            FROM pricelist pl
            WHERE pl.intname = %(intname)s
            """,
            {"intname": PLUGIN_NAME}
        ).one_or_none()
        return pricelist
    except Exception as e:
        LOGGER.error(f"Ошибка получения pricelist: {e}")
        return None


def _get_enumeration(intname):
    try:
        db = get_db("billmgr")
        enumeration = db.select_query(
            """
            SELECT e.*
            FROM enumeration e
            WHERE e.intname = %(intname)s
            """,
            {"intname": intname}
        ).one_or_none()
        return enumeration
    except Exception as e:
        LOGGER.error(f"Ошибка получения enumeration {intname}: {e}")
        return None


def _get_active_projects():
    try:
        db = get_db("billmgr")
        projects = db.select_query(
            """
            SELECT pj.*
            FROM project pj
            WHERE pj.active = 'on'
            """
        ).all()
        return projects
    except Exception as e:
        LOGGER.error(f"Ошибка получения активных проектов: {e}")
        return []


def _get_datacenters():
    try:
        db = get_db("billmgr")
        datacenters = db.select_query(
            """
            SELECT dc.*
            FROM datacenter dc
            WHERE external_id IS NULL
            """
        ).all()
        return datacenters
    except Exception as e:
        LOGGER.error(f"Ошибка получения datacenters: {e}")
        return []


def _options_prompt(options: list, message: str, key_field: str = 'id', label_field: str = 'name', default=None, type_=None):
    if not options:
        click.echo("Нет доступных опций для выбора")
        return None
        
    choices = click.Choice([str(o[key_field]) for o in options])
    first_option_key = options[0][key_field]
    default_option_key = default if default is not None else first_option_key

    def format_choice(option):
        choice_string = f" [{option[key_field]}] - {option[label_field]}"
        if option[key_field] == default_option_key: 
            choice_string += " (по умолчанию)"
        return choice_string

    default_choice = str(default_option_key)
    choices_string = "\n".join([format_choice(o) for o in options])
    input_value = click.prompt(
        f"{message}\n{choices_string}\n",
        default=default_choice,
        type=choices,
        show_default=False,
        show_choices=False,
    )
    if type_ is not None:
        return type_(input_value)
    return input_value


def _create_itemtype():
    click.echo("Создание itemtype...")
    
    try:
        itemtype = _get_itemtype()
        
        if not itemtype:
            mgrctl_exec([
                "itemtype.edit",
                f"intname={PLUGIN_NAME}",
                f"name={PLUGIN_NAME.title()}",
                f"name_ru={PLUGIN_NAME.title()}",
                "nostopholidays=on",
                "closetype=1",
                "closesubtype=0",
                "monthly=on",
                "quarterly=on",
                "semiannual=on",
                "annually=on",
                "sok=ok",
            ])
            click.echo(f"ItemType {PLUGIN_NAME} создан")
        else:
            click.echo(f"ItemType {PLUGIN_NAME} уже существует")
            
    except Exception as e:
        LOGGER.error(f"Ошибка создания itemtype: {e}")
        click.echo(f"Ошибка создания itemtype: {e}")


def _create_processingmodule():
    click.echo("Создание processing module...")
    
    try:
        processingmodule = _get_processingmodule()
        
        if not processingmodule:
            datacenters = _get_datacenters()
            if datacenters:
                datacenter_id = _options_prompt(
                    datacenters,
                    f"Выберите datacenter для processing module '{PLUGIN_NAME}'",
                    key_field="id",
                    label_field="name",
                    type_=int,
                )
            else:
                datacenter_id = click.prompt("Введите ID datacenter", type=int, default=1)
            
            mgrctl_exec([
                "processing.add.settings",
                f"module={MODULE_NAME}",
                f"type={PLUGIN_NAME}",
                f"name={PLUGIN_NAME.title()}",
                f"datacenter={datacenter_id}",
                "sok=ok",
                "out=xml",
            ])
            click.echo(f"Processing module {MODULE_NAME} создан")
        else:
            click.echo(f"Processing module {MODULE_NAME} уже существует")
            
    except Exception as e:
        LOGGER.error(f"Ошибка создания processing module: {e}")
        click.echo(f"Ошибка создания processing module: {e}")


def _create_enumerations():
    click.echo("Создание перечислений...")
    
    enumerations = [
        {
            "intname": f"{PLUGIN_NAME}_status",
            "name": f"{PLUGIN_NAME.title()} Status",
            "name_ru": f"Статус {PLUGIN_NAME}",
            "items": [
                EnumerationItem("active", "Active", "Активен"),
                EnumerationItem("inactive", "Inactive", "Неактивен"),
                EnumerationItem("suspended", "Suspended", "Приостановлен"),
            ]
        }
    ]
    
    try:
        for enum_data in enumerations:
            _create_enumeration(
                enum_data["intname"],
                enum_data["name"],
                enum_data["name_ru"],
                enum_data["items"]
            )
    except Exception as e:
        LOGGER.error(f"Ошибка создания перечислений: {e}")
        click.echo(f"Ошибка создания перечислений: {e}")


def _create_enumeration(intname, name, name_ru, items: List[EnumerationItem]):
    try:
        enumeration = _get_enumeration(intname)
        
        if not enumeration:
            mgrctl_exec([
                "enumeration.edit",
                f"intname={intname}",
                f"name={name}",
                f"name_ru={name_ru}",
                "sok=ok",
            ])
            
            enumeration = _get_enumeration(intname)
            
            if enumeration and items:
                for item in items:
                    mgrctl_exec([
                        "enumerationitem.edit",
                        f"plid={enumeration['id']}",
                        f"intname={item.intname}",
                        f"name={item.name}",
                        f"name_ru={item.name_ru}",
                        "sok=ok",
                    ])
            
            click.echo(f"Перечисление {intname} создано")
        else:
            click.echo(f"Перечисление {intname} уже существует")
            
    except Exception as e:
        LOGGER.error(f"Ошибка создания перечисления {intname}: {e}")
        click.echo(f"Ошибка создания перечисления {intname}: {e}")


def _create_pricelist():
    click.echo("Создание pricelist...")
    
    try:
        pricelist = _get_pricelist()
        
        if not pricelist:
            processingmodule = _get_processingmodule()
            itemtype = _get_itemtype()
            
            if not processingmodule:
                click.echo("Processing module не найден. Создайте его сначала.")
                return
                
            if not itemtype:
                click.echo("ItemType не найден. Создайте его сначала.")
                return
            
            active_projects = _get_active_projects()
            if active_projects:
                project_id = _options_prompt(
                    active_projects,
                    "Выберите проект для создания pricelist",
                    key_field="id",
                    label_field="name",
                    type_=int,
                )
            else:
                project_id = click.prompt("Введите ID проекта", type=int, default=1)
            
            mgrctl_exec([
                "pricelist.add.step2",
                f"name_ru={PLUGIN_NAME.title()}",
                f"name={PLUGIN_NAME.title()}",
                f"intname={PLUGIN_NAME}",
                f"processingmodule={processingmodule['id']}",
                f"itemtype={itemtype['id']}",
                f"project={project_id}",
                "activate=off",
                "billdaily=on",
                "billhourly=off",
                "chargestoped=off",
                "hidden=on",
                "monthly126=0",
                "quarterly126=0",
                "semiannual126=0",
                "annually126=0",
                "sok=ok",
            ])
            
            import time
            time.sleep(0.5)
            pricelist = _get_pricelist()
            
            if pricelist:
                click.echo(f"Pricelist {PLUGIN_NAME} создан (ID: {pricelist['id']})")
            else:
                click.echo(f"Pricelist {PLUGIN_NAME} создан, но не найден в БД")
        else:
            click.echo(f"Pricelist {PLUGIN_NAME} уже существует")
            
    except Exception as e:
        LOGGER.error(f"Ошибка создания pricelist: {e}")
        click.echo(f"Ошибка создания pricelist: {e}")


def _edit_prices():
    click.echo("Редактирование цен...")
    
    try:
        pricelist = _get_pricelist()
        
        if not pricelist:
            click.echo("Pricelist не найден. Создайте его сначала.")
            return
        
        base_price = click.prompt("Введите базовую цену", type=float, default=0.0)
        
        mgrctl_exec([
            "pricelist.edit",
            f"elid={pricelist['id']}",
            f"stat126={base_price}",
            "sok=ok",
        ])
        
        click.echo(f"Цена установлена: {base_price}")
        
    except Exception as e:
        LOGGER.error(f"Ошибка редактирования цен: {e}")
        click.echo(f"Ошибка редактирования цен: {e}")


def _activate_pricelist():
    """Активация pricelist"""
    click.echo("Активация pricelist...")
    
    try:
        pricelist = _get_pricelist()
        
        if not pricelist:
            click.echo("Pricelist не найден.")
            return
        
        is_active = pricelist.get("active") == "on"
        
        if is_active:
            click.echo("Pricelist уже активен")
        else:
            if click.confirm("Активировать pricelist?"):
                mgrctl_exec([
                    "pricelist.resume",
                    f"elid={pricelist['id']}"
                ])
                click.echo("Pricelist активирован")
            else:
                click.echo("Активация pricelist пропущена")
                
    except Exception as e:
        LOGGER.error(f"Ошибка активации pricelist: {e}")
        click.echo(f"Ошибка активации pricelist: {e}") 
'''

    def _get_i18n_base_enum_template(self) -> str:
        return '''from abc import ABC


class I18nValue(ABC):
    pass

class I18nEnum:
    def __iter__(self):
        for name, value in vars(self).items():
            if isinstance(value, I18nValue) or not name.startswith("_"):
                yield value
'''

    def _get_i18n_factory_template(self) -> str:
        return '''from fluent_compiler.bundle import FluentBundle
from billmgr_addon.fluentbillmgr import FluentTranslator, TranslatorHub


class Language:
    RU: str = 'ru'
    EN: str = 'en'

def i18n_factory(project_path: str) -> TranslatorHub:
    return TranslatorHub(
        locales_map={Language.RU: (Language.RU, Language.EN), Language.EN: Language.EN},
        translators=[
            FluentTranslator(
                locale=Language.RU,
                translator=FluentBundle.from_files(
                    locale=Language.RU,
                    filenames=[f"{project_path}/app/i18n/locales/ru/LC_MESSAGES/txt.ftl"],
                ),
            ),
            FluentTranslator(
                locale=Language.EN,
                translator=FluentBundle.from_files(
                    locale=Language.EN,
                    filenames=[f"{project_path}/app/i18n/locales/en/LC_MESSAGES/txt.ftl"],
                ),
            ),
        ],
        root_locale=Language.RU,
    )

'''

    def _get_i18n_script_template(self) -> str:
        return '''#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import sys
from billmgr_addon.fluentbillmgr.cli import cli

if __name__ == "__main__":
    if sys.argv[0].endswith("-script.pyw"):
        sys.argv[0] = sys.argv[0][:-11]
    elif sys.argv[0].endswith(".exe"):
        sys.argv[0] = sys.argv[0][:-4]
    sys.exit(cli())
'''

    def _get_i18n_stub_script_template(self) -> str:
        return '''#!/usr/bin/env bash
DIR="$(dirname "$0")"
export PYTHONPATH="$DIR/../.."
"$DIR/i18n.py" -ftl "$DIR/locales/en/LC_MESSAGES/txt.ftl" -stub "$DIR/stub.pyi"

'''

    def _get_i18n_stub_template(self) -> str:
        return '''from typing import Literal

    
class TranslatorRunner:
    def get(self, path: str, **kwargs) -> str: ...
    
    test: Test


class Test:
    @staticmethod
    def name() -> Literal["""Test name"""]: ...


'''

    def _get_i18n_en_locale_template(self) -> str:
        return '''test-name = Test name
'''

    def _get_i18n_ru_locale_template(self) -> str:
        return '''test-name = Тестовое имя
'''

    def _get_readme_template(self) -> str:
        return '''# ${project_name}

## 📋 Требования

- Python 3.8
- BILLmanager 5
- MySQL/MariaDB (для работы с БД BILLmanager)


## Конфигурация

Скопируйте конфигурационные файлы и настройте их:

```bash
cp config.example.toml config.toml
cp deploy.example.toml deploy.toml
```

Отредактируйте `config.toml`:
```toml
DEBUG = false
FORWARDED_SECRET = 'SECRET_FROM_BILLMGR_CONF'
BILLMGR_API_URL = 'https://localhost:1500/billmgr'
BILLMGR_API_USE_INTERFACE = ''
```

## Установка плагина

```bash
# Полная установка на сервере
python cli.py install

# Или поэтапная установка
python cli.py install_plugin
```

## CLI Команды

Плагин предоставляет несколько CLI команд для управления:

## Команды системы установки

Полное создание сущностей BILLmanager:

#### CLI команды:
- `python cli.py install` - **Полная установка** (Plugin + Processing Module + ItemType + Pricelist + Enumerations)
- `python cli.py install_plugin` - Установка только плагина
- `python cli.py install_processing_module` - Установка только processing module  
- `python cli.py check` - Проверка состояния всех компонентов
- `python cli.py uninstall` - Удаление плагина

#### Что создается при полной установке:
1. **Plugin** - веб-интерфейс плагина
2. **Processing Module** - обработчик событий услуг
3. **ItemType** - тип услуги для биллинга
4. **Enumerations** - перечисления для параметров
5. **Pricelist** - прайс-лист с настройками биллинга

### Основные команды

```bash
# Тестирование работы плагина
python cli.py test

# Полная установка плагина
python cli.py install

# Установка только плагина (без processing module)
python cli.py install_plugin

# Проверка состояния установки
python cli.py check

# Удаление плагина
python cli.py uninstall

# Перезапуск панели BILLmanager
python cli.py restart_panel
```

### Processing Module команды

```bash
# Просмотр доступных processing module команд
python processing_module_cli.py --help

# Выполнение команды processing module
python processing_module_cli.py <command> [args]
```

### Команды для работы с переводами

```bash
# Генерация stub файлов для типизации переводов
cd app/i18n
./i18n_stub_script.sh

# Или вручную
python app/i18n/i18n.py -ftl app/i18n/locales/en/LC_MESSAGES/txt.ftl -stub app/i18n/stub.pyi
```

#### С командами деплоя можно ознакомиться в описании пакета billmgr-addon


## Структура проекта

```
${project_name}/
├── app/                          # Основное приложение
│   ├── __init__.py
│   ├── app.py                   # Фабрики Flask приложений
│   ├── endpoints/               # Эндпоинты плагина
│   │   ├── __init__.py
│   │   └── example.py
│   ├── services/                # Бизнес-логика
│   │   ├── __init__.py
│   │   ├── billmgr.py          # Работа с API BILLmanager
│   │   └── example.py
│   ├── i18n/                    # Система интернационализации
│   │   ├── __init__.py
│   │   ├── base_enum.py         # Базовые классы для enum
│   │   ├── factory.py           # Фабрика для создания i18n
│   │   ├── i18n.py             # CLI скрипт для работы с переводами
│   │   ├── i18n_stub_script.sh # Скрипт генерации stub файлов
│   │   ├── stub.pyi            # Типизация для IDE
│   │   └── locales/            # Переводы
│   │       ├── en/LC_MESSAGES/
│   │       │   └── txt.ftl     # Английские переводы
│   │       └── ru/LC_MESSAGES/
│   │           └── txt.ftl     # Русские переводы
│   └── blueprints/              # Flask blueprints
│       ├── __init__.py
│       ├── cli/                 # CLI команды
│       │   ├── __init__.py
│       │   ├── commands.py      # Общие команды
│       │   └── installation.py  # Система установки
│       └── processing_module/   # Processing module
│           ├── __init__.py
│           └── features.py
├── xml/                         # XML конфигурация
│   └── src/
│       ├── main.xml
│       ├── example_list.xml
│       └── processing_module.xml
├── cli.py                       # CLI точка входа
├── cgi.py                       # CGI точка входа
├── processing_module_cli.py     # Processing module CLI
├── build_xml.py                 # Сборка XML файлов
├── config.toml                  # Конфигурация
├── deploy.toml                  # Конфигурация развертывания
└── requirements.txt             # Зависимости
```

### Логи

Логи плагина сохраняются в:
- `logs/app.log` - основные логи приложения
- Логи BILLmanager в `/usr/local/mgr5/var/billmgr.log`

## Разработка

### Добавление новых эндпоинтов

1. Создайте новый файл в `app/endpoints/`
2. Добавьте эндпоинт в `app/endpoints/__init__.py`
3. Создайте соответствующий XML файл в `xml/src/`
4. Пересоберите XML: `python build_xml.py`

### Добавление новых CLI команд

1. Добавьте функцию в `app/blueprints/cli/commands.py`
2. Зарегистрируйте команду в `app/blueprints/cli/__init__.py`

### Processing Module

Processing module используется для обработки событий услуг в BILLmanager. Команды добавляются в `app/blueprints/processing_module/features.py`.

### Работа с переводами

1. **Добавьте новые ключи в файлы переводов:**
   ```fluent
   # app/i18n/locales/ru/LC_MESSAGES/txt.ftl
   new-feature = Новая функция
   
   # app/i18n/locales/en/LC_MESSAGES/txt.ftl
   new-feature = New feature
   ```

2. **Обновите stub файлы для типизации:**
   ```bash
   cd app/i18n && ./i18n_stub_script.sh
   ```

3. **Используйте переводы в коде:**
   ```python
   feature_name = i18n.new.feature()
   ```

### Интернационализация и локализация

Проект использует систему интернационализации на основе **Fluent**

#### Файлы переводов

Переводы хранятся в формате Fluent (.ftl). Формат поддерживает параметры, плюрализацию и сложные языковые конструкции:

**app/i18n/locales/ru/LC_MESSAGES/txt.ftl:**
```fluent
test-name = Тестовое имя
user-greeting = Привет, { $name }!
item-count = У вас { $count ->
    [one] { $count } элемент
    [few] { $count } элемента
   *[other] { $count } элементов
}
```

**app/i18n/locales/en/LC_MESSAGES/txt.ftl:**
```fluent
test-name = Test name
user-greeting = Hello, { $name }!
item-count = You have { $count ->
    [one] { $count } item
   *[other] { $count } items
}
```

#### Использование в коде

```python
# В эндпоинтах
from typing import TYPE_CHECKING
from billmgr_addon.core.i18n import TranslatorRunner

if TYPE_CHECKING:
    from app.i18n.stub import TranslatorRunner

class ExampleList(ListEndpoint):
    async def get(self, mgr_list: MgrList, mgr_request: MgrRequest):
        i18n: TranslatorRunner = mgr_request.i18n
        
        # Использование переводов
        name = i18n.test.name()  # Типизированный доступ
        greeting = i18n.get("user-greeting", name="Пользователь")  # С параметрами
        count_msg = i18n.get("item-count", count=5)  # Плюрализация
```

#### Добавление новых переводов

1. Добавьте ключи в файлы переводов (`app/i18n/locales/*/LC_MESSAGES/txt.ftl`)
2. Обновите типизацию:
   ```bash
   cd app/i18n
   ./i18n_stub_script.sh
   ```

#### Поддерживаемые языки

- **Русский (ru)** - основной язык
- **Английский (en)** - язык по умолчанию

#### Добавление нового языка

1. Создайте папку: `app/i18n/locales/{lang}/LC_MESSAGES/`
2. Добавьте файл переводов: `txt.ftl`
3. Обновите `app/i18n/factory.py`

'''
