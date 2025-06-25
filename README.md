# BILLmanager Addon Framework

Универсальная Python-библиотека для создания плагинов BILLmanager.

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
pip install git+https://github.com/billmanager/billmgr-addon.git
```

### Для разработки

```bash
git clone https://github.com/billmanager/billmgr-addon.git
cd billmgr-addon
pip install -e .
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
pip install -e .
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

## CLI команды

### Создание проекта

```bash
billmgr-addon create-project <name> [--path=.] [--template=basic]
```

### Установка плагина

```bash
sudo billmgr-addon install --plugin-name <name>
```

### Установка модуля обработки

```bash
sudo billmgr-addon install-processing-module --module-name <name>
```

### Сборка XML

```bash
billmgr-addon build-xml
```

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

## Расширения

### Дополнительные возможности

```bash
# Поддержка Celery
pip install billmgr-addon[celery]

# Поддержка WebSocket
pip install billmgr-addon[websockets]

# Инструменты разработки
pip install billmgr-addon[dev]
```

## Примеры

Смотрите примеры в директории `examples/`:

- `basic-plugin/` - базовый плагин со списком и формой
- `api-integration/` - интеграция с внешним API
- `processing-module/` - модуль обработки услуг

## Документация

Полная документация доступна по адресу: [https://billmgr-addon.readthedocs.io](https://billmgr-addon.readthedocs.io)

## Поддержка

- **Issues**: [GitHub Issues](https://github.com/billmanager/billmgr-addon/issues)
- **Документация**: [ReadTheDocs](https://billmgr-addon.readthedocs.io)
- **Примеры**: [GitHub Examples](https://github.com/billmanager/billmgr-addon/tree/main/examples)

## Лицензия

MIT License. См. файл [LICENSE](LICENSE) для подробностей.

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

## Changelog

См. файл [CHANGELOG.md](CHANGELOG.md) для истории изменений. 