# -*- coding: utf-8 -*-

"""
Конфигурация Gunicorn для продакшен развертывания

Использование:
    gunicorn -c gunicorn.conf.py wsgi:app
"""

import multiprocessing
import os

# Сервер
bind = "unix:/run/billmgr-plugin.sock"  # Unix socket для Nginx
# bind = "0.0.0.0:8000"  # Или TCP порт

# Воркеры
workers = multiprocessing.cpu_count() * 2 + 1
worker_class = "sync"  # Можно использовать "gevent" для async
worker_connections = 1000
max_requests = 1000
max_requests_jitter = 50

# Таймауты
timeout = 300  # 5 минут для длительных операций
graceful_timeout = 30
keepalive = 5

# Пути
pythonpath = os.path.dirname(os.path.abspath(__file__))
chdir = pythonpath

# Логирование
accesslog = "-"  # stdout
errorlog = "-"   # stderr
loglevel = "info"
access_log_format = '%(h)s %(l)s %(u)s %(t)s "%(r)s" %(s)s %(b)s "%(f)s" "%(a)s" %(D)s'

# Процесс
daemon = False  # Управляется systemd
pidfile = "/run/billmgr-plugin.pid"
user = "www-data"
group = "www-data"
umask = 0o022

# Безопасность
limit_request_line = 4094
limit_request_fields = 100
limit_request_field_size = 8190

# Server mechanics
preload_app = True  # Загружаем приложение до форка воркеров
reload = False      # Отключено в продакшене


def on_starting(server):
    """Вызывается при старте сервера"""
    server.log.info("Starting BILLmanager plugin WSGI server")


def on_reload(server):
    """Вызывается при перезагрузке"""
    server.log.info("Reloading BILLmanager plugin WSGI server")


def when_ready(server):
    """Вызывается когда сервер готов принимать соединения"""
    server.log.info("BILLmanager plugin WSGI server is ready. Listening at: %s", server.address)


def worker_int(worker):
    """Вызывается при получении воркером INT или QUIT"""
    worker.log.info("Worker received INT or QUIT signal")


def pre_fork(server, worker):
    """Вызывается перед форком воркера"""
    server.log.info("Worker spawning (pid: %s)", worker.pid)


def post_fork(server, worker):
    """Вызывается после форка воркера"""
    server.log.info("Worker spawned (pid: %s)", worker.pid)


def worker_abort(worker):
    """Вызывается при аварийном завершении воркера"""
    worker.log.info("Worker received SIGABRT signal")