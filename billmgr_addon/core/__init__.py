# -*- coding: utf-8 -*-

"""
Ядро плагина

Предоставляет основные компоненты для создания плагинов:
- Система маршрутизации (MgrRouter)
- UI компоненты (MgrForm, MgrList, MgrError)
- Типы запросов и ответов
- Базовые классы эндпоинтов
"""

from types import SimpleNamespace
import tomlkit
from Crypto.PublicKey import RSA

from flask import Flask, appcontext_pushed, g
from flask_login import LoginManager

from billmgr_addon.auth.auth import load_billmgr_user
from billmgr_addon.core.error_handlers import register_error_handlers
from billmgr_addon.db.db import DBConfig, FlaskDbExtension
from billmgr_addon.utils.files import config_path, public_path
from billmgr_addon.utils.logging import LOGGER, setup_logger
from billmgr_addon.utils.serialization import CustomJSONEncoder


def get_router():
    """Получить экземпляр роутера из контекста Flask"""
    extension_namespace = getattr(g, MgrAddonExtension.namespace_id)
    return extension_namespace.router


class MgrAddonExtension:
    """
    Расширение Flask для работы с BILLmanager плагинами

    Предоставляет систему маршрутизации, UI компоненты и интеграцию с BILLmanager.
    """

    namespace_id = "_mgr_addon"

    def __init__(self):
        self.router = None

    def init_app(self, app: Flask, endpoints):
        """
        Инициализировать расширение с Flask приложением

        Args:
            app: Flask приложение
            endpoints: Список эндпоинтов плагина
        """
        from .router import MgrRouter

        self.router = MgrRouter(app, endpoints)

        appcontext_pushed.connect(self.appcontext_pushed_handler, app)
        app.teardown_appcontext(self.teardown_appcontext_handler)

        LOGGER.debug(
            f'MgrAddonExtension extension initialized with "{MgrAddonExtension.namespace_id}" namespace'
        )

    def appcontext_pushed_handler(self, sender):
        """Обработчик создания контекста приложения"""
        try:
            extension_namespace = SimpleNamespace()
            extension_namespace.router = self.router
            setattr(g, MgrAddonExtension.namespace_id, extension_namespace)
        except Exception as e:
            LOGGER.exception(e)

    def teardown_appcontext_handler(self, error):
        """Обработчик завершения контекста приложения"""
        extension_namespace = getattr(g, MgrAddonExtension.namespace_id)

    def on_extension_close(self):
        """Обработчик закрытия расширения"""
        LOGGER.debug(
            f'MgrAddonExtension extension with "{MgrAddonExtension.namespace_id}" namespace is closed'
        )


def create_common_app():
    """
    Создать базовое Flask приложение для плагина

    Returns:
        Flask: Настроенное приложение
    """
    app = Flask(__name__)

    app.config.from_file(config_path, load=tomlkit.load)

    is_debugging = app.config.get('DEBUG', False)

    app.json_encoder = CustomJSONEncoder
    app.mgr_encryption_key = RSA.importKey(open('/usr/local/mgr5/etc/billmgr.pem').read())

    billmgr_db_config = DBConfig.from_panel_name('billmgr')

    FlaskDbExtension().init_app(app)
    FlaskDbExtension() \
        .init_app(app, billmgr_db_config, alias='billmgr')

    # FIXME - make simpler Celery setup
    # celery_app_name = 'cloud_addon'
    # CeleryExtension().init_app(app, task_prefix=celery_app_name, include=[
    #     'app.celery.cloud.servers',
    #     'app.celery.cloud.ssh_keys',
    #     'app.celery.cloud.volumes',
    #     'app.celery.cloud.ips',
    #     # 'app.celery.cloud.loadbalancers',
    #     'app.celery.cloud.vrouters',
    #     # 'app.celery.cloud.db_clusters',
    #     'app.celery.cloud.project',
    # ], broker_use_ssl={
    #     'keyfile': cwd_path.joinpath(app.config['CELERY_BROKER_KEYFILE']),
    #     'certfile': cwd_path.joinpath(app.config['CELERY_BROKER_CERTFILE']),
    #     'ca_certs': cwd_path.joinpath(app.config['CELERY_BROKER_CA_CERTFILE']),
    #     'cert_reqs': ssl.CERT_REQUIRED
    # })


    return app

def create_app(endpoints) -> Flask:
    app = create_common_app()
    app.static_folder = public_path

    MgrAddonExtension().init_app(app, endpoints)
    register_error_handlers(app)

    login_manager = LoginManager()
    login_manager.init_app(app)
    login_manager.request_loader(load_billmgr_user)

    # from app.blueprints.main import bp as main_bp
    # app.register_blueprint(main_bp)

    return app

def create_cgi_app(endpoints):
    """
    Создать CGI приложение с эндпоинтами

    Args:
        endpoints: Список эндпоинтов

    Returns:
        Flask: Настроенное CGI приложение
    """
    app = create_common_app()
    app.static_folder = public_path

    MgrAddonExtension().init_app(app, endpoints)
    register_error_handlers(app)

    login_manager = LoginManager()
    login_manager.init_app(app)
    login_manager.request_loader(load_billmgr_user)

    return app


def create_cli_app():
    """
    Создать CLI приложение

    Returns:
        Flask: Настроенное CLI приложение
    """
    app = create_common_app()
    return app


__all__ = ["MgrAddonExtension", "get_router", "create_app", "create_cgi_app", "create_cli_app"]
