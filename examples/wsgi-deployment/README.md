# Развертывание плагина через WSGI

Этот пример показывает, как развернуть BILLmanager плагин через WSGI для продакшен использования.

## Преимущества WSGI

- **Производительность** - WSGI серверы оптимизированы для высоких нагрузок
- **Масштабируемость** - легко запустить несколько воркеров
- **Надежность** - автоматический перезапуск при сбоях
- **Мониторинг** - встроенные метрики и логирование

## Gunicorn

### Установка

```bash
pip install gunicorn
```

### Запуск

```bash
# Простой запуск с 4 воркерами
gunicorn -w 4 wsgi:app

# С настройками для продакшена
gunicorn \
    --workers 4 \
    --bind 0.0.0.0:8000 \
    --timeout 300 \
    --access-logfile /var/log/plugin/access.log \
    --error-logfile /var/log/plugin/error.log \
    --log-level info \
    wsgi:app
```

### Systemd сервис

Создайте файл `/etc/systemd/system/billmgr-plugin.service`:

```ini
[Unit]
Description=BILLmanager Plugin WSGI Server
After=network.target

[Service]
Type=notify
User=www-data
Group=www-data
WorkingDirectory=/opt/billmgr-plugin
Environment="PATH=/opt/billmgr-plugin/venv/bin"
ExecStart=/opt/billmgr-plugin/venv/bin/gunicorn \
    --workers 4 \
    --bind unix:/run/billmgr-plugin.sock \
    --timeout 300 \
    --access-logfile - \
    --error-logfile - \
    wsgi:app
Restart=always

[Install]
WantedBy=multi-user.target
```

## uWSGI

### Установка

```bash
pip install uwsgi
```

### Запуск

```bash
# Простой запуск
uwsgi --http :8000 --wsgi-file wsgi.py --callable app

# С настройками для продакшена
uwsgi \
    --http :8000 \
    --wsgi-file wsgi.py \
    --callable app \
    --processes 4 \
    --threads 2 \
    --stats :9191 \
    --log-file /var/log/plugin/uwsgi.log
```

### Конфигурационный файл

Создайте `uwsgi.ini`:

```ini
[uwsgi]
module = wsgi:app
master = true
processes = 4
threads = 2

socket = /run/billmgr-plugin.sock
chmod-socket = 666
vacuum = true

die-on-term = true
log-file = /var/log/plugin/uwsgi.log
```

Запуск с конфигурацией:

```bash
uwsgi --ini uwsgi.ini
```

## Nginx прокси

Настройте Nginx для проксирования запросов к WSGI серверу:

```nginx
server {
    listen 80;
    server_name plugin.example.com;

    location / {
        proxy_pass http://unix:/run/billmgr-plugin.sock;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        
        # Таймауты для длительных операций
        proxy_connect_timeout 300s;
        proxy_send_timeout 300s;
        proxy_read_timeout 300s;
    }
}
```

## Мониторинг

### Проверка статуса

```bash
# Gunicorn
systemctl status billmgr-plugin

# Логи
journalctl -u billmgr-plugin -f

# Метрики uWSGI
uwsgi --connect-and-read :9191
```

### Healthcheck endpoint

Добавьте эндпоинт для проверки здоровья:

```python
from billmgr_addon import ActionEndpoint, MgrRequest, MgrSuccessResponse

class HealthCheck(ActionEndpoint):
    """Проверка состояния плагина"""
    
    async def get(self, mgr_request: MgrRequest):
        # Проверяем подключение к БД
        try:
            from billmgr_addon import get_db
            db = get_db('billmgr')
            db.select_query("SELECT 1").one()
            
            return MgrSuccessResponse(msg="OK")
        except Exception as e:
            return MgrErrorResponse(msg=f"Database check failed: {e}")

# Добавьте в список эндпоинтов
endpoints = [
    # ... другие эндпоинты
    HealthCheck("health"),
]
```

## Оптимизация производительности

1. **Количество воркеров**: `(2 x CPU) + 1`
2. **Таймаут**: увеличьте для длительных операций
3. **Буферизация**: используйте Nginx для статики
4. **Кеширование**: добавьте Redis для частых запросов

## Troubleshooting

### Плагин не запускается

```bash
# Проверьте импорты
python -c "from wsgi import app"

# Проверьте права доступа
ls -la /run/billmgr-plugin.sock

# Проверьте логи
tail -f /var/log/plugin/error.log
```

### 502 Bad Gateway

- Проверьте, что WSGI сервер запущен
- Проверьте путь к сокету в Nginx и WSGI конфигурации
- Увеличьте таймауты в Nginx

### Высокая нагрузка

- Увеличьте количество воркеров
- Включите потоки в uWSGI
- Используйте async эндпоинты в плагине 