# Базовый плагин

Пример простого плагина BILLmanager с использованием billmgr-addon framework.

## Функции

- Список элементов
- Форма создания/редактирования
- Базовые действия

## Установка

1. Создайте виртуальное окружение:
   ```bash
   python -m venv venv
   source venv/bin/activate
   ```

2. Установите зависимости:
   ```bash
   pip install billmgr-addon
   ```

3. Настройте config.toml

4. Установите плагин:
   ```bash
   sudo billmgr-addon install --plugin-name basic_plugin
   sudo systemctl restart billmgr
   ```

## Структура

- `basic_plugin/` - основной пакет
- `xml/` - XML конфигурация
- `cgi.py` - CGI точка входа
- `cli.py` - CLI точка входа 