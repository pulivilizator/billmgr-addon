from types import SimpleNamespace
from typing import Callable

from flask import Flask, current_app

from billmgr_addon.utils.logging import LOGGER

from ..fluentbillmgr import TranslatorHub, TranslatorRunner
from ..utils.files import cwd_path


def get_i18n(locale: str) -> TranslatorRunner:
    i18n: TranslatorHub = current_app.extensions["i18n"].namespace.instance
    return i18n.get_translator_by_locale(locale)


class I18nExtension:
    def __init__(self):
        self._namespace = None
        self.app = None

    def init_app(self, app: Flask, i18n_factory: Callable[[str], TranslatorHub]):
        self.app = app
        self.i18n_factory = i18n_factory
        app.extensions["i18n"] = self
        app.teardown_appcontext(self.teardown_appcontext_handler)

        self._init_i18n()
        LOGGER.debug("I18nExtension initialized")

    def _init_i18n(self):
        ns = SimpleNamespace()
        i18n_obj = self.i18n_factory(str(cwd_path))
        ns.instance = i18n_obj
        self._namespace = ns

    @property
    def namespace(self):
        if self._namespace is None:
            self._init_i18n()
        return self._namespace

    def teardown_appcontext_handler(self, error):
        pass

def register_i18n_for_app(i18n_factory: Callable[[str], TranslatorHub]):
    """
    Декоратор для регистрации i18n фабрики в Flask приложении.
    
    Args:
        i18n_factory: Функция-фабрика для создания TranslatorHub
    
    Returns:
        Декорированная функция создания приложения
    """
    def decorator(create_app_func):
        def wrapper(*args, **kwargs):
            app = create_app_func(*args, **kwargs)
            I18nExtension().init_app(app, i18n_factory)
            return app
        return wrapper
    return decorator