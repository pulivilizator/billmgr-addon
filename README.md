# BILLmanager Addon Framework

Универсальная Python-библиотека для создания плагинов BILLmanager.

📖 **Новичок?** Начните с [Руководства разработчика](DEVELOPER_GUIDE.md) - подробного пошагового туториала по созданию вашего первого плагина.

## Описание

BILLmanager Addon Framework предоставляет готовый набор инструментов для разработки плагинов биллинга:

- **Ядро плагина** - система маршрутизации, эндпоинтов и UI компонентов
- **Работа с БД** - удобная интеграция с базой данных BILLmanager
- **Авторизация** - готовая система авторизации через сессии биллинга
- **CLI инструменты** - команды для создания проектов и установки
- **Генератор проектов** - быстрое создание базовой структуры плагина
- **XML сборка** - автоматическая сборка XML конфигурации

## Установка

### Из Git репозитория

```bash
# Основная версия с PyMySQL (рекомендуется для разработки)
pip install "git+ssh://git@github.com/path/billmgr-addon.git#egg=billmgr-addon[pymysql]"

# С mysqlclient (для продакшена, требует системные библиотеки MySQL)
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

### 1. Создание нового проекта

```bash
billmgr-addon create-project my-plugin
cd my-plugin
```

### 2. Настройка окружения

```bash
python -m venv venv
source venv/bin/activate

# Установка зависимостей проекта с PyMySQL (рекомендуется)
pip install -e ".[pymysql]"

# Альтернативно: установка с mysqlclient (требует системные библиотеки)
pip install -e ".[mysqlclient]"
```

### 3. Конфигурация

Скопируйте `config.example.toml` в `config.toml` и настройте параметры:

```toml
DEBUG = false
FORWARDED_SECRET = 'SECRET_FROM_BILLMGR_CONF'
BILLMGR_API_URL = 'https://localhost:1500/billmgr'
```

### 4. Установка в BILLmanager

```bash
sudo billmgr-addon install --plugin-name my_plugin
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
│   └── services/           # Бизнес-логика
│       └── example.py
├── xml/                    # XML конфигурация
│   └── src/
│       ├── main.xml
│       └── example_list.xml
├── tests/                  # Тесты
├── cgi.py                  # CGI точка входа
├── cli.py                  # CLI точка входа
├── wsgi.py                 # WSGI точка входа
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

### Формы

```python
from billmgr_addon import FormEndpoint, MgrForm, MgrRequest

class MyForm(FormEndpoint):
    async def get(self, form: MgrForm, mgr_request: MgrRequest):
        # Настройка формы
        return form
    
    async def setvalues(self, form: MgrForm, mgr_request: MgrRequest):
        # Обработка отправки формы
        return form
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

### Сервисы

```python
class MyService:
    def get_data(self):
        # Бизнес-логика
        return []
    
    def create_item(self, name: str):
        # Создание элемента
        pass
```

### Processing Module (Модуль обработки услуг)

**Processing module** - это специальный тип плагина BILLmanager для автоматизации жизненного цикла услуг. Он позволяет интегрировать внешние системы (облачные платформы, API) с биллингом для автоматического управления услугами.

**Когда используется:**
- Услуги хостинга (VPS, серверы, домены)
- Облачные сервисы (проекты, хранилища, БД)
- Лицензии программного обеспечения
- Любые услуги с внешним API

**Основные возможности:**
- Автоматическое создание услуг при оплате
- Приостановка при просрочке платежа
- Возобновление после оплаты задолженности
- Удаление отменённых услуг
- Сбор статистики использования для начислений

```python
# Прямой импорт (пока ленивые импорты в разработке)
from billmgr_addon.core.processing import ProcessingModule, OpenCommand
from billmgr_addon.core.response import MgrOkResponse

class MyOpenCommand(OpenCommand):
    async def execute(self, item_id: int = None, **kwargs):
        # Создание услуги
        print(f"Создание услуги #{item_id}")
        # Здесь можно обращаться к внешним API, БД и т.д.
        return MgrOkResponse()

# Создание модуля
module = ProcessingModule("myservice")
module.register_open(MyOpenCommand())

# Использование в processing_module_cli.py:
from billmgr_addon.core.processing import create_processing_module_app
app = create_processing_module_app(module)
```

**Доступные команды:**
- `open` - создание услуги
- `resume` - возобновление приостановленной услуги  
- `suspend` - приостановка услуги
- `close` - удаление услуги
- `start/stop` - запуск/остановка (отличается от resume/suspend)
- `stat` - сбор статистики
- `features` - описание возможностей модуля

## CLI команды

### Создание проекта

```bash
billmgr-addon create-project my-plugin [--path=.] [--template=basic]
```

Создает новый проект плагина с базовой структурой.

### Сборка XML

```bash
billmgr-addon build-xml
```

Собирает XML файлы из `xml/src/` в `xml/build.xml`. Выполняется автоматически перед установкой.

### Локальная установка плагина

```bash
sudo billmgr-addon install --plugin-name my_plugin
```

Устанавливает плагин в локальный BILLmanager. Создает ссылки:
- `/usr/local/mgr5/addon/my_plugin` → CGI обработчик
- `/usr/local/mgr5/cgi/my_plugin` → дублирующая ссылка  
- `/usr/local/mgr5/etc/xml/billmgr_mod_my_plugin.xml` → XML конфигурация

**Откуда берет данные:**
- Пути проекта: из текущей директории (должен выполняться в корне проекта)
- Пути BILLmanager: фиксированные `/usr/local/mgr5/`
- Интерпретатор Python: `./venv/bin/python3`

### Установка модуля обработки

```bash
sudo billmgr-addon install-processing-module --module-name my_module
```

Устанавливает модуль обработки услуг. Создает ссылки:
- `/usr/local/mgr5/processing/pmmy_module` → CLI обработчик
- `/usr/local/mgr5/etc/xml/billmgr_mod_pmmy_module.xml` → XML конфигурация

**Структура файлов для processing module:**
```
my-plugin/
├── processing_module_cli.py    # CLI точка входа  
├── xml/processing_module.xml   # XML конфигурация
└── my_plugin/
    └── processing_module.py    # Реализация команд
```

## Команды деплоя

Группа расширенных команд для управления плагинами:

### Установка с дополнительными опциями

```bash
sudo billmgr-addon deploy install --plugin-name my_plugin [--force]
```

Расширенная установка с возможностью принудительной перезаписи.

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
  ✓ Addon handler: /usr/local/mgr5/addon/my_plugin
  ✓ CGI handler: /usr/local/mgr5/cgi/my_plugin  
  ✓ XML config: /usr/local/mgr5/etc/xml/billmgr_mod_my_plugin.xml
Плагин полностью установлен
```

### Сервер разработки

```bash
billmgr-addon deploy dev-server [--host=localhost] [--port=5000] [--debug]
```

Запускает Flask сервер для отладки плагина без установки в BILLmanager.

### Удаленный деплой

```bash
billmgr-addon deploy remote-deploy -e dev --plugin-name my_plugin [--config deploy.toml]
```

Выполняет полный деплой плагина на удаленный сервер:
- Создает бэкап на сервере
- Синхронизирует файлы через rsync
- Устанавливает зависимости
- Устанавливает плагин в BILLmanager

Доступные опции:
- `--environment/-e` - окружение (dev, staging, prod)
- `--plugin-name` - имя плагина для установки
- `--config/-c` - путь к файлу конфигурации (по умолчанию deploy.toml)
- `--backup/--no-backup` - создавать ли бэкап (по умолчанию да)
- `--install/--no-install` - устанавливать ли плагин (по умолчанию да)  
- `--restart-billmgr/--no-restart-billmgr` - перезапускать ли BILLmanager
- `--dry-run` - показать команды без выполнения

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

Пример использования:

```bash
# Деплой на dev с проверкой команд
billmgr-addon deploy remote-deploy -e dev --plugin-name my_plugin --dry-run

# Деплой на prod с полной установкой
billmgr-addon deploy remote-deploy -e prod --plugin-name my_plugin --restart-billmgr

# Деплой только файлов без установки плагина
billmgr-addon deploy remote-deploy -e staging --plugin-name my_plugin --no-install
```

### Требования для удаленного деплоя

1. **SSH доступ** к серверу с ключами
2. **rsync** на локальной машине и сервере  
3. **Python и venv** на сервере
4. **sudo права** для установки плагина
5. **BILLmanager** установленный на сервере

## XML конфигурация

Библиотека автоматически собирает XML файлы из директории `xml/src/`:

```xml
<?xml version="1.0" encoding="UTF-8"?>
<mgrdata>
    <handler name="my_plugin" type="xml">
        <func name="example.list" />
    </handler>

    <mainmenu level="user">
        <node name="my_plugin">
            <node name="example.list" action="example.list" type="list"/>
        </node>
    </mainmenu>

    <import path="example_list.xml"/>
</mgrdata>
```

## Авторизация

Библиотека предоставляет готовую интеграцию с системой авторизации BILLmanager:

```python
from billmgr_addon import load_billmgr_user

# В конфигурации Flask-Login
login_manager.request_loader(load_billmgr_user)
```

## WSGI интерфейс

Библиотека поддерживает развертывание через WSGI для продакшен окружения:

```python
# wsgi.py
from pathlib import Path
from billmgr_addon import create_wsgi_app

app = create_wsgi_app(
    plugin_name='my_plugin',
    plugin_path=Path(__file__).parent,
    config_path=Path(__file__).parent / 'config.toml'
)
```

Запуск через Gunicorn:

```bash
gunicorn -w 4 -b 127.0.0.1:8000 wsgi:app
```

Подробнее смотрите в [примере WSGI развертывания](examples/wsgi-deployment/).

## Расширения

### Дополнительные возможности

```bash
# Доступные extras для установки:

# PyMySQL драйвер (Pure Python, простая установка)
pip install "git+https://github.com/username/billmgr-addon.git[pymysql]"

# mysqlclient драйвер (C-extension, быстрее, но требует системные библиотеки)
pip install "git+https://github.com/username/billmgr-addon.git[mysqlclient]"

# Поддержка Celery для фоновых задач
pip install "git+https://github.com/username/billmgr-addon.git[celery]"

# Поддержка WebSocket
pip install "git+https://github.com/username/billmgr-addon.git[websockets]"

# Инструменты разработки (mypy, ruff, pytest)
pip install "git+https://github.com/username/billmgr-addon.git[dev]"

# Полная установка со всеми возможностями
pip install "git+https://github.com/username/billmgr-addon.git[full]"

# Комбинирование extras
pip install "git+https://github.com/username/billmgr-addon.git[pymysql,celery,dev]"
```


## Примеры

Смотрите примеры в директории `examples/`:

- `basic-plugin/` - базовый плагин со списком и формой
- `wsgi-deployment/` - развертывание через WSGI для продакшена
- `deploy.example.toml` - пример конфигурации удаленного деплоя
- `processing-module-example.py` - пример модуля обработки услуг


## Разработка

### Настройка окружения разработки

```bash
git clone https://github.com/billmanager/billmgr-addon.git
cd billmgr-addon
python -m venv venv
source venv/bin/activate
pip install -e .[dev]
```

### Запуск тестов

```bash
pytest
```

### Линтинг

```bash
ruff check .
mypy .
```