# # -*- coding: utf-8 -*-

# """
# Конфигурация Gunicorn

# """

# import multiprocessing
# import os


# workers = multiprocessing.cpu_count() * 2 + 1
# worker_class = "sync"
# worker_connections = 1000
# max_requests = 1000
# max_requests_jitter = 50

# timeout = 300
# graceful_timeout = 30
# keepalive = 5

# pythonpath = os.path.dirname(os.path.abspath(__file__))
# chdir = pythonpath

# accesslog = "-"
# errorlog = "-"
# loglevel = "info"
# access_log_format = '%(h)s %(l)s %(u)s %(t)s "%(r)s" %(s)s %(b)s "%(f)s" "%(a)s" %(D)s'

# daemon = False
# pidfile = "/run/billmgr-plugin.pid"
# user = "www-data"
# group = "www-data"
# umask = 0o022

# limit_request_line = 4094
# limit_request_fields = 100
# limit_request_field_size = 8190

# preload_app = True
# reload = False


# def on_starting(server):
#     server.log.info("Starting BILLmanager plugin WSGI server")


# def on_reload(server):
#     server.log.info("Reloading BILLmanager plugin WSGI server")


# def when_ready(server):
#     server.log.info("BILLmanager plugin WSGI server is ready. Listening at: %s", server.address)


# def worker_int(worker):
#     worker.log.info("Worker received INT or QUIT signal")


# def pre_fork(server, worker):
#     server.log.info("Worker spawning (pid: %s)", worker.pid)


# def post_fork(server, worker):
#     server.log.info("Worker spawned (pid: %s)", worker.pid)


# def worker_abort(worker):
#     worker.log.info("Worker received SIGABRT signal")
