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
            self.project_path / "tests",
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
            "setup.py": self._get_setup_py_template(),
            "README.md": self._get_readme_template(),
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
            # XML файлы
            "xml/src/main.xml": self._get_main_xml_template(),
            "xml/src/example_list.xml": self._get_example_list_xml_template(),
            # Точки входа
            "cgi.py": self._get_cgi_template(),
            "cli.py": self._get_cli_template(),
            "wsgi.py": self._get_wsgi_template(),
            "build_xml.py": self._get_build_xml_template(),
            # Тесты
            "tests/__init__.py": "",
            "tests/test_example.py": self._get_test_template(),
        }

    def _get_setup_py_template(self) -> str:
        return """#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from setuptools import setup, find_packages

setup(
    name='${project_name}',
    version='0.1.0',
    description='BILLmanager plugin: ${project_name}',
    packages=find_packages(where='app'),
    package_dir={'': 'app'},
    python_requires='>=3.8',
    install_requires=[
        'billmgr-addon>=0.1.0',
    ],
    entry_points={
        'console_scripts': [
            '${plugin_name}-cli=app.app:create_cli_app',
        ],
    },
)
"""

    def _get_requirements_template(self) -> str:
        return """billmgr-addon>=0.1.0
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
# Сервер для разработки
server = "root@dev.example.com"
app_folder = "/opt/${plugin_name}"
public_folder = "/usr/local/mgr5/skins/userdata/${plugin_name}"
ssh_options = "-A"

[prod]
# Продакшен сервер
server = "deploy@production.example.com"
app_folder = "/opt/${plugin_name}"
public_folder = "/usr/local/mgr5/skins/userdata/${plugin_name}"
ssh_options = "-A -i ~/.ssh/production_key"
"""

    def _get_readme_template(self) -> str:
        return """# ${project_name}

BILLmanager плагин: ${project_name}

## Структура проекта

```
${project_name}/
├── app/                    # Основная логика плагина
│   ├── endpoints/          # Обработчики запросов
│   ├── services/           # Бизнес-логика
│   └── app.py             # Фабрики Flask приложений
├── xml/                    # XML конфигурация
│   ├── src/               # Исходники XML
│   └── build.xml          # Собранный XML (генерируется)
├── public/                 # Статические файлы
├── tests/                  # Тесты
├── cgi.py                 # CGI точка входа
├── cli.py                 # CLI точка входа
├── wsgi.py                # WSGI точка входа
├── config.toml            # Конфигурация (создать из config.example.toml)
└── deploy.toml            # Конфигурация деплоя (создать из deploy.example.toml)
```

## Установка

1. Создайте виртуальное окружение:
   ```bash
   python -m venv venv
   source venv/bin/activate
   ```

2. Установите зависимости:
   ```bash
   pip install -r requirements.txt
   ```

3. Скопируйте конфигурационные файлы:
   ```bash
   cp config.example.toml config.toml
   cp deploy.example.toml deploy.toml
   ```

4. Установите плагин в BILLmanager:
   ```bash
   sudo billmgr-addon deploy install --plugin-name ${plugin_name}
   ```

## Сборка XML

```bash
billmgr-addon build-xml
```

## Удаленный деплой

1. Настройте серверы в deploy.toml
2. Выполните деплой:
   ```bash
   billmgr-addon deploy remote-deploy -e dev/prod --plugin-name ${plugin_name}
   ```

Доступные команды деплоя:
- `remote-deploy` - полный деплой на удаленный сервер
- `status` - проверка статуса установки
- `uninstall` - удаление плагина
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

__version__ = '0.1.0'
__all__ = ['endpoints']
'''

    def _get_app_template(self) -> str:
        return '''# -*- coding: utf-8 -*-

"""
Фабрики Flask приложений для ${project_name}
"""

from billmgr_addon import create_app as create_app_base, create_cgi_app as create_cgi_app_base, create_cli_app as create_cli_app_base
from .endpoints import endpoints


def create_cgi_app():
    """Создать CGI приложение для плагина"""
    return create_cgi_app_base(endpoints)


def create_cli_app():
    """Создать CLI приложение для плагина"""  
    return create_cli_app_base()


def create_app():
    """Создать основное Flask приложение для плагина"""
    app = create_app_base()
    # Здесь можно добавить дополнительную конфигурацию
    return app

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

from billmgr_addon import ListEndpoint, MgrList, MgrRequest


class ExampleList(ListEndpoint):
    """Пример списка для демонстрации"""
    
    async def get(self, mgr_list: MgrList, mgr_request: MgrRequest):
        """Получить данные для списка"""
        
        # Пример данных
        sample_data = [
            {"id": 1, "name": "Элемент 1", "status": "active"},
            {"id": 2, "name": "Элемент 2", "status": "inactive"},
        ]
        
        mgr_list.set_data_rows(sample_data)
        return mgr_list
'''

    def _get_example_service_template(self) -> str:
        return '''# -*- coding: utf-8 -*-

from typing import List, Dict, Any


class ExampleService:
    """Пример сервиса для бизнес-логики"""
    
    def get_items(self) -> List[Dict[str, Any]]:
        """Получить список элементов"""
        return [
            {"id": 1, "name": "Элемент 1", "status": "active"},
            {"id": 2, "name": "Элемент 2", "status": "inactive"},
        ]
    
    def create_item(self, name: str) -> Dict[str, Any]:
        """Создать новый элемент"""
        return {"id": 3, "name": name, "status": "active"}
'''

    def _get_main_xml_template(self) -> str:
        return """<?xml version="1.0" encoding="UTF-8"?>
<mgrdata>
    <handler name="${plugin_name}" type="xml">
        <func name="example.list" />
    </handler>

    <mainmenu level="user">
        <node name="${plugin_name}" after="customer">
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
        <coldata>
            <col name="id" type="data" hidden="yes" />
            <col name="name" type="data" />
            <col name="status" type="data" />
        </coldata>
    </metadata>

    <lang name="ru">
        <messages name="example.list">
            <msg name="title">Пример списка</msg>
            <msg name="name">Название</msg>
            <msg name="status">Статус</msg>
        </messages>
    </lang>
    <lang name="en">
        <messages name="example.list">
            <msg name="title">Example List</msg>
            <msg name="name">Name</msg>
            <msg name="status">Status</msg>
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

import sys
from pathlib import Path

# Добавляем текущую директорию в Python path
sys.path.insert(0, str(Path(__file__).parent))

# Импортируем приложение из папки app
from app.app import create_cgi_app

if __name__ == '__main__':
    app = create_cgi_app()
    # Используем универсальный CGI обработчик
    from billmgr_addon.cgi import run_with_cgi
    run_with_cgi(app)
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

    def _get_wsgi_template(self) -> str:
        return '''#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
WSGI интерфейс для ${project_name}
"""

import sys
from pathlib import Path

# Добавляем текущую директорию в Python path
sys.path.insert(0, str(Path(__file__).parent))

# Импортируем приложение из папки app
from app.app import create_app

# Создаем WSGI приложение
app = create_app()

# Для запуска через Gunicorn:
# gunicorn -w 4 -b 127.0.0.1:8000 wsgi:app

# Для запуска через uWSGI:
# uwsgi --http :8000 --wsgi-file wsgi.py --callable app --processes 4

# Для разработки можно использовать встроенный сервер Flask:
if __name__ == '__main__':
    app.run(debug=True, port=8000)
'''

    def _get_build_xml_template(self) -> str:
        return '''#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Сборщик XML конфигурации для ${project_name}
"""

import sys
from pathlib import Path

# Добавляем текущую директорию в Python path
sys.path.insert(0, str(Path(__file__).parent))

# Используем универсальный сборщик XML
from billmgr_addon.build_xml import main

if __name__ == '__main__':
    main()
'''

    def _get_test_template(self) -> str:
        return '''# -*- coding: utf-8 -*-

import pytest
from app.services.example import ExampleService


def test_example_service():
    """Тест примера сервиса"""
    service = ExampleService()
    items = service.get_items()
    
    assert len(items) == 2
    assert items[0]['name'] == 'Элемент 1'


def test_create_item():
    """Тест создания элемента"""
    service = ExampleService()
    item = service.create_item('Новый элемент')
    
    assert item['name'] == 'Новый элемент'
    assert item['status'] == 'active'
'''
