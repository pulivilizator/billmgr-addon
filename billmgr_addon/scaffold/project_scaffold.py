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
        key_files = ["setup.py", "app/__init__.py", "cgi.py", "cli.py", "xml/src/main.xml"]

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
            self.project_path / "app" / "processing_module",
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
            # Processing Module
            "app/processing_module/__init__.py": "",
            "app/processing_module/handler.py": self._get_processing_module_handler_template(),
            "processing_module_cli.py": self._get_processing_module_cli_template(),
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
    create_processing_module_cli_app,
    create_processing_module_blueprint,
    LOGGER
)
from billmgr_addon.utils.logging import setup_logger
from .endpoints import endpoints
from .processing_module.handler import ${class_name}ProcessingModuleHandler


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
    return create_cli_app_base()

def create_processing_module_cli_app():
    """Создать CLI приложение для processing module"""
    
    # Настройка логгирования для processing module
    logger = setup_logger(
        name=billmgr_addon.LOGGER_NAME,
        path=None,
        filename='app.log', 
        debug=False, 
        remove_default_handlers=True,
        enable_console=True  # Для CLI включаем консольный вывод
    )
    
    billmgr_addon.LOGGER = logger
    
    try:
        # Создание обработчика и blueprint
        handler = ${class_name}ProcessingModuleHandler()
        blueprint = create_processing_module_blueprint(handler)
        
        # Создание CLI приложения с blueprint
        app = create_processing_module_cli_app(blueprint)
        
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

    def _get_processing_module_handler_template(self) -> str:
        return '''# -*- coding: utf-8 -*-

"""
Processing Module Handler для ${project_name}
"""

from typing import Dict, List

from billmgr_addon import ProcessingModuleHandler, ProcessingModuleResponse, LOGGER


class ${class_name}ProcessingModuleHandler(ProcessingModuleHandler):
    """
    Обработчик processing module для ${project_name}
    """

    def get_itemtypes(self) -> List[Dict[str, str]]:
        """Типы услуг которые обрабатывает модуль"""
        return [{"name": "${plugin_name}_service"}]

    def get_features(self) -> List[Dict[str, str]]:
        """Поддерживаемые команды"""
        return [
            {"name": "features"},
            {"name": "open"},
            {"name": "suspend"},
            {"name": "resume"},
            {"name": "close"},
            {"name": "stat"},
        ]

    def get_params(self) -> List[Dict[str, str]]:
        """Параметры конфигурации"""
        return [
            {"name": "api_url"},
            {"name": "api_token", "crypted": "yes"},
        ]

    def open_command(self, item_id=None, runningoperation=None, **kwargs) -> ProcessingModuleResponse:
        """Обработка команды open - активация услуги"""
        LOGGER.info(f"Opening service {item_id} for project ${project_name}")
        
        try:
            # Здесь разместите логику активации услуги
            # Например, вызов API для создания ресурса
            
            LOGGER.info(f"Service {item_id} opened successfully")
            return ProcessingModuleResponse("ok")
            
        except Exception as e:
            LOGGER.exception(f"Error opening service {item_id}: {e}")
            return ProcessingModuleResponse("error")

    def suspend_command(self, item_id=None, runningoperation=None, **kwargs) -> ProcessingModuleResponse:
        """Обработка команды suspend - приостановка услуги"""
        LOGGER.info(f"Suspending service {item_id} for project ${project_name}")
        
        try:
            # Здесь разместите логику приостановки услуги
            # Например, вызов API для остановки ресурса
            
            LOGGER.info(f"Service {item_id} suspended successfully")
            return ProcessingModuleResponse("ok")
            
        except Exception as e:
            LOGGER.exception(f"Error suspending service {item_id}: {e}")
            return ProcessingModuleResponse("error")

    def resume_command(self, item_id=None, runningoperation=None, **kwargs) -> ProcessingModuleResponse:
        """Обработка команды resume - возобновление услуги"""
        LOGGER.info(f"Resuming service {item_id} for project ${project_name}")
        
        try:
            # Здесь разместите логику возобновления услуги
            
            LOGGER.info(f"Service {item_id} resumed successfully")
            return ProcessingModuleResponse("ok")
            
        except Exception as e:
            LOGGER.exception(f"Error resuming service {item_id}: {e}")
            return ProcessingModuleResponse("error")

    def close_command(self, item_id=None, runningoperation=None, **kwargs) -> ProcessingModuleResponse:
        """Обработка команды close - закрытие услуги"""
        LOGGER.info(f"Closing service {item_id} for project ${project_name}")
        
        try:
            # Здесь разместите логику закрытия услуги
            
            LOGGER.info(f"Service {item_id} closed successfully")
            return ProcessingModuleResponse("ok")
            
        except Exception as e:
            LOGGER.exception(f"Error closing service {item_id}: {e}")
            return ProcessingModuleResponse("error")

    def stat_command(self, module_id=None, **kwargs) -> ProcessingModuleResponse:
        """Обработка команды stat - сбор статистики"""
        LOGGER.info(f"Collecting stats for module {module_id} in project ${project_name}")
        
        try:
            # Здесь разместите логику сбора статистики
            
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

from app import create_processing_module_cli_app

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
            <type name="${plugin_name}_service"/>
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
                    <input type="text" name="api_url" check="url" required="yes" maxlength="256"/>
                </field>
                <field name="api_token">
                    <input type="text" name="api_token" required="yes" maxlength="256"/>
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
