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


### Локальная разработка

```bash
git clone https://github.com/path/billmgr-addon.git
cd billmgr-addon
python -m venv venv
source venv/bin/activate
pip install -e ".[dev,pymysql]"
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
billmgr-addon create-project
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

- Для установки без деплоя(находясь на сервере)

```bash
sudo billmgr-addon install --plugin-name PLUGIN_NAME
sudo systemctl restart billmgr
```

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

1. **Создайте обработчик команд**:

```python
from billmgr_addon import ProcessingModuleHandler, ProcessingModuleResponse

class MyServiceProcessingModuleHandler(ProcessingModuleHandler):
    def get_itemtypes(self):
        return [{"name": "myservice"}]
    
    def get_features(self):
        return [
            {"name": "features"},
            {"name": "open"},
            {"name": "suspend"},
            {"name": "resume"},
            {"name": "close"},
            {"name": "stat"},
        ]
    
    def get_params(self):
        return [
            {"name": "api_url"},
            {"name": "api_token", "crypted": "yes"},
        ]
    
    def open_command(self, item_id=None, **kwargs):
        # Логика активации услуги
        return ProcessingModuleResponse("ok")
```

2. **Создайте Blueprint и CLI приложение**:

```python
from billmgr_addon import create_processing_module_blueprint, create_processing_module_cli_app

handler = MyServiceProcessingModuleHandler()
blueprint = create_processing_module_blueprint(handler)

def create_processing_module_cli_app():
    return create_processing_module_cli_app(blueprint)
```

3. **Создайте CLI точку входа** (`processing_module_cli.py`):

```python
#!/usr/bin/env python
from app import create_processing_module_cli_app

if __name__ == "__main__":
    app = create_processing_module_cli_app()
    with app.app_context():
        app.cli.commands['execute']()
```

4. **Создайте XML конфигурацию** (`xml/src/processing_module.xml`):

```xml
<?xml version='1.0' encoding="UTF-8"?>
<mgrdata>
    <plugin name="pmmyservice">
        <group>processing_module</group>
        <params>
            <type name="myservice"/>
        </params>
    </plugin>
    
    <metadata name="processing.edit.pmmyservice" type="form">
        <form title="name">
            <page name="connect">
                <field name="api_url">
                    <input type="text" name="api_url" required="yes"/>
                </field>
            </page>
        </form>
    </metadata>
</mgrdata>
```


## CLI команды

У всех команд есть флаг `--help`
Подробнее с командами можно ознакомиться в [deploy.py](./billmgr_addon/cli/deploy.py) и [main.py](./billmgr_addon/cli/main.py)

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