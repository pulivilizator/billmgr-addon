## Описание

- **Ядро плагина** - система маршрутизации, эндпоинтов и UI компонентов
- **Работа с БД** - интеграция с базой данных BILLmanager
- **Авторизация** - система авторизации через сессии биллинга
- **CLI инструменты** - команды для создания проектов и установки
- **Генератор проектов** - создание базовой структуры плагина
- **XML сборка** - сборка XML конфигурации
- **Processing Module** - модули обработки услуг

## Установка

### Из Git репозитория

```bash
# Версия с PyMySQL
pip install "git+ssh://git@github.com/path/billmgr-addon.git#egg=billmgr-addon[pymysql]"

# С mysqlclient
pip install "git+ssh://git@github.com/path/billmgr-addon.git#egg=billmgr-addon[mysqlclient]"

# Минимальная установка (без MySQL драйверов)
pip install "git+ssh://git@github.com/path/billmgr-addon.git"
```


## Быстрый старт

### 1. Настройка окружения

```bash
python -m venv venv
source venv/bin/activate
pip install "git+ssh://git@github.com/path/billmgr-addon.git"
```

### 2. Создание нового проекта

```bash
billmgr-addon create-project --name NAME
```

### 3. Настройка путей (опционально)

Для настройки путей к конфигурации, логам и другим ресурсам создайте файл `settings.py`:

```python
"""
Настройки путей для плагина.
"""

# Корневая директория проекта
PROJECT_ROOT = "."

# Путь к файлу конфигурации
CONFIG_PATH = "config.toml"

# Путь к директории с публичными файлами
PUBLIC_PATH = "public"

# Путь к директории с логами
LOGS_PATH = "logs"
```

### 4. Конфигурация

Скопируйте `config.example.toml` в `config.toml` и настройте параметры.

### 5. Установка в BILLmanager

- Для установки с локального ПК необходимо заполнить файл `deploy.toml` и выполнить команду 
```bash
billmgr-addon deploy remote-deploy -e dev/prod --plugin-name PLUGIN_NAME
```

### 6. Установка с настойкой processing_module
Установка происходит в `app/blueprints/cli/installation.py`. Перед установкой стоит ознакомиться с кодом и изменить необходимые параметры.



## Структура проекта

```
my-plugin/
├── my_plugin/              # Основной пакет плагина
│   ├── __init__.py
│   ├── app.py              # Фабрики Flask приложений
│   ├── endpoints/          # Эндпоинты плагина
│   │   ├── __init__.py
│   │   └── example.py
│   ├── services/           # Бизнес-логика
│   │   └── example.py
│   └── processing_module/  # Processing Module
│       ├── __init__.py
│       └── handler.py
├── xml/                    # XML конфигурация
│   └── src/
│       ├── main.xml
│       ├── example_list.xml
│       └── processing_module.xml
├── cgi.py                  # CGI точка входа
├── cli.py                  # CLI точка входа
├── processing_module_cli.py # Processing Module CLI
├── config.example.toml     # Пример конфигурации
└── setup.py               # Настройки пакета
```

## Основные компоненты

### Эндпоинты

```python
from billmgr_addon import ListEndpoint, MgrList, MgrRequest

class MyList(ListEndpoint):
    async def get(self, mgr_list: MgrList, mgr_request: MgrRequest):
        data = [
            {"id": 1, "name": "Item 1", "status": "active"},
            {"id": 2, "name": "Item 2", "status": "inactive"},
        ]
        mgr_list.set_data_rows(data)
        return mgr_list
```

### Работа с БД

```python
from billmgr_addon import get_db

def get_items():
    db = get_db('billmgr')
    return db.select_query("""
        SELECT * FROM my_table
        WHERE status = %(status)s
    """, {"status": "active"}).all()
```

### Логгирование

Логгирование конфигурируется встроенной функцией setup_logger(как вариант), и можно переназначить переменную billmgr-addon.LOGGER чтоб видеть логи пакета billmgr-addon.

```python
    logger = setup_logger(
        name=billmgr_addon.LOGGER_NAME,
        path=None,
        filename='app.log', 
        debug=False, 
        remove_default_handlers=True,
        enable_console=False
    )
    
    
    billmgr_addon.LOGGER = logger
```

### Расширение эндпоинтов для специфичных задач

Если плагину нужна дополнительная авторизация или обработка (например, проверка проектов, подписок), можно создать базовые классы:

```python
from billmgr_addon import MgrEndpoint, get_db, MgrErrorResponse

class ProjectRequiredEndpoint(MgrEndpoint):
    """Базовый класс для эндпоинтов, требующих активный проект"""
    
    async def _handle_request(self, mgr_request):
        # Проверяем наличие проекта у пользователя
        project_id = self._get_user_project(mgr_request.auth_user)
        if not project_id:
            return MgrErrorResponse("Project not found")
        
        # Добавляем project_id в запрос
        mgr_request.project_id = project_id
        
        # Выполняем основную логику
        return await super()._handle_request(mgr_request)
    
    def _get_user_project(self, user_id):
        db = get_db('billmgr')
        # Ваша логика получения проекта
        return "project_123"

class MyCloudEndpoint(ProjectRequiredEndpoint):
    async def get(self, mgr_request):
        # mgr_request.project_id уже доступен
        return f"Project: {mgr_request.project_id}"
```

## Processing Module

### Создание Processing Module

Processing Module использует архитектуру Flask Blueprint'ов с CLI командами для обработки событий услуг в BILLmanager.

1. **Создайте Blueprint** (`app/blueprints/processing_module/__init__.py`):

```python
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
def execute(command, subcommand, pricelist_id, item_id, module_id, param, value, runningoperation, level, user_id):
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
```

2. **Создайте обработчики команд** (`app/blueprints/processing_module/features.py`):

```python
import xml.etree.ElementTree as ET
from billmgr_addon import MgrResponse, ProcessingModuleResponse, LOGGER

class FeaturesResponse(MgrResponse):
    """Ответ на команду features"""
    
    def __init__(self, itemtype_name: str) -> None:
        super().__init__()
        
        itemtypes = [{"name": itemtype_name}]
        
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
    return FeaturesResponse("myservice")


def open_command(item_id=None, runningoperation=None, **kwargs):
    """Команда open - активация услуги"""
    LOGGER.info(f"Opening service {item_id}")
    
    try:
        # Логика активации услуги
        # Здесь можно получить настройки API из БД:
        # from app.services.billmgr import get_myservice_api_credentials
        # api_url, api_token = get_myservice_api_credentials()
        
        LOGGER.info(f"Service {item_id} opened successfully")
        return ProcessingModuleResponse("ok")
        
    except Exception as e:
        LOGGER.exception(f"Error opening service {item_id}: {e}")
        return ProcessingModuleResponse("error")


def suspend_command(item_id=None, runningoperation=None, **kwargs):
    """Команда suspend - приостановка услуги"""
    LOGGER.info(f"Suspending service {item_id}")
    
    try:
        # Логика приостановки услуги
        LOGGER.info(f"Service {item_id} suspended successfully")
        return ProcessingModuleResponse("ok")
        
    except Exception as e:
        LOGGER.exception(f"Error suspending service {item_id}: {e}")
        return ProcessingModuleResponse("error")


def resume_command(item_id=None, runningoperation=None, **kwargs):
    """Команда resume - возобновление услуги"""
    LOGGER.info(f"Resuming service {item_id}")
    
    try:
        # Логика возобновления услуги
        LOGGER.info(f"Service {item_id} resumed successfully")
        return ProcessingModuleResponse("ok")
        
    except Exception as e:
        LOGGER.exception(f"Error resuming service {item_id}: {e}")
        return ProcessingModuleResponse("error")


def close_command(item_id=None, runningoperation=None, **kwargs):
    """Команда close - закрытие услуги"""
    LOGGER.info(f"Closing service {item_id}")
    
    try:
        # Логика закрытия услуги
        LOGGER.info(f"Service {item_id} closed successfully")
        return ProcessingModuleResponse("ok")
        
    except Exception as e:
        LOGGER.exception(f"Error closing service {item_id}: {e}")
        return ProcessingModuleResponse("error")


def start_command(item_id=None, runningoperation=None, **kwargs):
    """Команда start - запуск услуги"""
    LOGGER.info(f"Starting service {item_id}")
    
    try:
        # Логика запуска услуги
        LOGGER.info(f"Service {item_id} started successfully")
        return ProcessingModuleResponse("ok")
        
    except Exception as e:
        LOGGER.exception(f"Error starting service {item_id}: {e}")
        return ProcessingModuleResponse("error")


def stop_command(item_id=None, runningoperation=None, **kwargs):
    """Команда stop - остановка услуги"""
    LOGGER.info(f"Stopping service {item_id}")
    
    try:
        # Логика остановки услуги
        LOGGER.info(f"Service {item_id} stopped successfully")
        return ProcessingModuleResponse("ok")
        
    except Exception as e:
        LOGGER.exception(f"Error stopping service {item_id}: {e}")
        return ProcessingModuleResponse("error")


def stat_command(module_id=None, **kwargs):
    """Команда stat - сбор статистики"""
    LOGGER.info(f"Collecting stats for module {module_id}")
    
    try:
        # Логика сбора статистики
        LOGGER.info(f"Stats collected successfully for module {module_id}")
        return ProcessingModuleResponse("ok")
        
    except Exception as e:
        LOGGER.exception(f"Error collecting stats for module {module_id}: {e}")
        return ProcessingModuleResponse("error")
```

3. **Интегрируйте в приложение** (`app/app.py`):

```python
import billmgr_addon
from billmgr_addon.core import create_common_app
from billmgr_addon.utils.logging import setup_logger
from .blueprints.processing_module import bp as processing_module_bp

def create_processing_module_cli_app():
    """Создать CLI приложение для processing module"""
    
    # Настройка логгирования
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
        raise
```

4. **Создайте CLI точку входа** (`processing_module_cli.py`):

```python
#!/usr/bin/env python
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
```

5. **Создайте XML конфигурацию** (`xml/src/processing_module.xml`):

```xml
<?xml version='1.0' encoding="UTF-8"?>
<mgrdata>
    <plugin name="pmmyservice">
        <group>processing_module</group>
        <author>Your Company</author>
        <params>
            <type name="myservice"/>
        </params>
        <msg name="desc_short" lang="ru">Мой сервис</msg>
        <msg name="desc_short" lang="en">My Service</msg>
        <msg name="desc_full" lang="ru">Модуль обработки для моего сервиса</msg>
        <msg name="desc_full" lang="en">Processing module for my service</msg>
    </plugin>
    
    <metadata name="processing.edit.pmmyservice" type="form">
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
        <messages name="processing.edit.pmmyservice">
            <msg name="api_url">URL API</msg>
            <msg name="api_token">Токен API</msg>
        </messages>
        <messages name="label_processing_modules">
            <msg name="pmmyservice">Мой сервис</msg>
            <msg name="module_pmmyservice">Мой сервис</msg>
        </messages>
    </lang>
    
    <lang name="en">
        <messages name="processing.edit.pmmyservice">
            <msg name="api_url">API URL</msg>
            <msg name="api_token">API Token</msg>
        </messages>
        <messages name="label_processing_modules">
            <msg name="pmmyservice">My Service</msg>
            <msg name="module_pmmyservice">My Service</msg>
        </messages>
    </lang>
</mgrdata>
```

6. **Добавьте импорт в main.xml**:

```xml
<import path="processing_module.xml"/>
```

### Логгирование в Processing Module

Processing Module использует глобальный `LOGGER` из `billmgr_addon` для единообразного логгирования:

```python
from billmgr_addon import LOGGER

def open_command(item_id=None, runningoperation=None, **kwargs):
    # Информационные сообщения
    LOGGER.info(f"Starting service activation for item {item_id}")
    
    # Отладочная информация
    LOGGER.debug(f"Command parameters: {kwargs}")
    
    try:
        # Логика обработки
        # Получение настроек из БД
        from app.services.billmgr import get_myservice_api_credentials
        api_url, api_token = get_myservice_api_credentials()
        
        # Ваша бизнес-логика
        pass
        
    except Exception as e:
        # Логгирование ошибок с полным стеком
        LOGGER.exception(f"Failed to activate service {item_id}: {e}")
        return ProcessingModuleResponse("error")
    
    LOGGER.info(f"Service {item_id} activated successfully")
    return ProcessingModuleResponse("ok")
```

### Получение настроек Processing Module

Создайте функцию для получения настроек модуля (`app/services/billmgr.py`):

```python
from billmgr_addon import get_db, LOGGER
from flask import current_app
import base64
from Crypto.Cipher import PKCS1_v1_5

def get_myservice_api_credentials() -> tuple:
    """Получает настройки API для processing module pmmyservice из БД BILLmanager"""
    db = get_db('billmgr')

    # Получение обычного параметра
    api_url_result = db.select_query(
        """
            SELECT pp.*
            FROM processingparam pp
            JOIN processingmodule pm
                ON pm.id = pp.processingmodule
                AND pm.module = 'pmmyservice'
            WHERE pp.intname = 'api_url'
        """).one_or_none()

    api_url = api_url_result['value'] if api_url_result else None

    # Получение зашифрованного параметра
    api_token_result = db.select_query(
        """
            SELECT pp.*
            FROM processingcryptedparam pp
            JOIN processingmodule pm
                ON pm.id = pp.processingmodule
                AND pm.module = 'pmmyservice'
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
```

## CLI команды

У всех команд есть флаг `--help`

Вызов команд происходит через `billmgr-addon` либо через `python cli.py`.

### Создание проекта

```bash
billmgr-addon create-project my-plugin [--path=.] [--template=basic]
```

Создает новый проект плагина с базовой структурой.

### Сборка XML

```bash
billmgr-addon build-xml [--xml-path PATH]
```

Собирает XML файлы из `xml/src/` в `xml/build.xml`. Выполняется автоматически перед установкой.

Опции:
- `--xml-path` - путь к папке xml (по умолчанию `./xml`)

### Локальная установка плагина

```bash
sudo billmgr-addon install --plugin-name my_plugin
```

Устанавливает плагин в BILLmanager. Создает ссылки:
- `/usr/local/mgr5/addon/my_plugin` → CGI обработчик
- `/usr/local/mgr5/cgi/my_plugin` → дублирующая ссылка  
- `/usr/local/mgr5/etc/xml/billmgr_mod_my_plugin.xml` → XML конфигурация

## Команды деплоя

Группа расширенных команд для управления плагинами:

### Установка с дополнительными опциями

```bash
sudo billmgr-addon deploy install --plugin-name my_plugin [--force] [--xml-path PATH]
```

Расширенная установка с возможностью принудительной перезаписи и указанием кастомного пути к XML файлам.

Опции:
- `--force` - принудительная перезапись существующих файлов
- `--xml-path` - путь к папке xml (по умолчанию `./xml`)

### Удаление плагина

```bash
sudo billmgr-addon deploy uninstall --plugin-name my_plugin
```

Полностью удаляет плагин из BILLmanager (удаляет все ссылки).

### Проверка статуса

```bash
billmgr-addon deploy status --plugin-name my_plugin
```

Показывает статус установки плагина:
```
Статус плагина my_plugin:
  Addon handler: /usr/local/mgr5/addon/my_plugin
  CGI handler: /usr/local/mgr5/cgi/my_plugin  
  XML config: /usr/local/mgr5/etc/xml/billmgr_mod_my_plugin.xml
Плагин полностью установлен
```

### Удаленный деплой

```bash
billmgr-addon deploy remote-deploy -e dev --plugin-name my_plugin [--config deploy.toml] [--xml-path PATH]
```

Выполняет полный деплой плагина на удаленный сервер:
- Создает бэкап на сервере
- Синхронизирует файлы через rsync
- Устанавливает зависимости
- Устанавливает плагин в BILLmanager

Доступные опции:
- `--environment/-e` - окружение (dev, prod)
- `--plugin-name` - имя плагина для установки
- `--config/-c` - путь к файлу конфигурации (по умолчанию deploy.toml)
- `--backup/--no-backup` - создавать ли бэкап (по умолчанию да)
- `--install/--no-install` - устанавливать ли плагин (по умолчанию да)  
- `--restart-billmgr/--no-restart-billmgr` - перезапускать ли BILLmanager
- `--dry-run` - показать команды без выполнения
- `--xml-path` - путь к папке xml (по умолчанию `./xml`)

**Конфигурация деплоя:**

Создайте файл `deploy.toml` в корне проекта:

```toml
[dev]
server = "root@dev.example.com"
app_folder = "/opt/my-plugin"
public_folder = "/usr/local/mgr5/skins/userdata/my-plugin"
ssh_options = "-A"

[prod]
server = "deploy@production.example.com"
app_folder = "/opt/my-plugin"
ssh_options = "-A -i ~/.ssh/production_key"
```

## Расширения

### Дополнительные возможности

```bash
# Доступные extras для установки:

# PyMySQL драйвер (Pure Python, простая установка)
pip install "git+ssh://git@github.com/path/billmgr-addon.git#egg=billmgr-addon[pymysql]"

# mysqlclient драйвер (C-extension, быстрее, но требует системные библиотеки)
pip install "git+ssh://git@github.com/path/billmgr-addon.git#egg=billmgr-addon[mysqlclient]"

# Поддержка Celery для фоновых задач
pip install "git+ssh://git@github.com/path/billmgr-addon.git#egg=billmgr-addon[celery]"

# Поддержка WebSocket
pip install "git+ssh://git@github.com/path/billmgr-addon.git#egg=billmgr-addon[websockets]"

# Инструменты разработки (mypy, ruff)
pip install "git+ssh://git@github.com/path/billmgr-addon.git#egg=billmgr-addon[dev]"

# Полная установка со всеми возможностями
pip install "git+ssh://git@github.com/path/billmgr-addon.git#egg=billmgr-addon[full]"

# Комбинирование extras
pip install "git+ssh://git@github.com/path/billmgr-addon.git#egg=billmgr-addon[pymysql,celery,dev]"
```