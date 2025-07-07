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
            "README.md": self._get_readme_template(),
            "requirements.txt": self._get_requirements_template(), # TODO: установка пакета с гитлаба
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
            # XML файлы
            "xml/src/main.xml": self._get_main_xml_template(),
            "xml/src/example_list.xml": self._get_example_list_xml_template(),
            # Точки входа
            "cgi.py": self._get_cgi_template(),
            "cli.py": self._get_cli_template(),
            "build_xml.py": self._get_build_xml_template(),
        }

    def _get_requirements_template(self) -> str:
        return """annotated-types==0.7.0
anyio==4.5.2
asgiref==3.8.1
attrs==25.3.0
babel==2.17.0
blinker==1.8.2
certifi==2025.6.15
charset-normalizer==3.4.2
click==8.1.8
exceptiongroup==1.3.0
flask==3.0.3
Flask-Login==0.6.3
fluent-compiler==1.1
fluent.syntax==0.19.0
h11==0.16.0
httpcore==1.0.9
httpx==0.28.1
idna==3.10
importlib-metadata==8.5.0
itsdangerous==2.2.0
jinja2==3.1.6
MarkupSafe==2.1.5
ordered-set==4.1.0
pycryptodome==3.23.0
pydantic==2.10.6
pydantic-core==2.27.2
PyMySQL==1.1.1
pytz==2025.2
requests==2.32.4
sniffio==1.3.1
tomlkit==0.13.3
typing-extensions==4.13.2
urllib3==2.2.3
watchdog==4.0.2
werkzeug==3.0.6
zipp==3.20.2
"""

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

    def _get_readme_template(self) -> str:
        return """# ${project_name}

BILLmanager плагин: ${project_name}

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
from billmgr_addon import create_app as create_app_base, create_cgi_app as create_cgi_app_base, create_cli_app as create_cli_app_base
from billmgr_addon.utils.logging import setup_logger
from .endpoints import endpoints


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
        return '''#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Сборщик XML конфигурации для testaddon
"""

import sys

from billmgr_addon.utils.xml_builder import XMLBuilder

def main():
    """Основная функция сборки XML"""
    try:
        builder = XMLBuilder()
        output_path = builder.build()
        print(f'XML успешно собран: {output_path}')
    except Exception as e:
        print(f'Ошибка сборки XML: {e}')
        sys.exit(1)

if __name__ == '__main__':
    main()

'''
