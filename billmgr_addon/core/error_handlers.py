# -*- coding: utf-8 -*-

"""
Обработчики ошибок для BILLmanager плагинов
"""

import logging

from flask import Flask, current_app, request

from .response import MgrErrorResponse, MgrUnknownErrorResponse


def register_error_handlers(app: Flask):
    """
    Регистрирует обработчики ошибок для Flask приложения

    Args:
        app: Flask приложение
    """

    @app.errorhandler(404)
    def handle_not_found(error):
        """Обработчик ошибки 404"""
        logging.warning(f"404 Not Found: {request.url}")
        return MgrErrorResponse("Resource not found", "NOT_FOUND").to_response(), 404

    @app.errorhandler(500)
    def handle_internal_error(error):
        """Обработчик внутренних ошибок сервера"""
        logging.exception(f"Internal Server Error: {error}")
        return MgrUnknownErrorResponse().to_response(), 500

    @app.errorhandler(403)
    def handle_forbidden(error):
        """Обработчик ошибки доступа"""
        logging.warning(f"403 Forbidden: {request.url}")
        return MgrErrorResponse("Access denied", "FORBIDDEN").to_response(), 403

    @app.errorhandler(400)
    def handle_bad_request(error):
        """Обработчик неверного запроса"""
        logging.warning(f"400 Bad Request: {request.url}")
        return MgrErrorResponse("Bad request", "BAD_REQUEST").to_response(), 400

    @app.errorhandler(Exception)
    def handle_exception(error):
        """Общий обработчик исключений"""
        logging.exception(f"Unhandled exception: {error}")

        # В режиме отладки возвращаем подробную информацию
        if current_app.debug:
            return MgrErrorResponse(str(error), "EXCEPTION").to_response(), 500
        else:
            return MgrUnknownErrorResponse().to_response(), 500


class BillmgrError(Exception):
    """Базовое исключение для ошибок BILLmanager"""

    def __init__(self, message, code=None):
        self.message = message
        self.code = code
        super().__init__(message)


class BillmgrAuthError(BillmgrError):
    """Ошибка авторизации BILLmanager"""

    pass


class BillmgrAPIError(BillmgrError):
    """Ошибка API BILLmanager"""

    pass


class BillmgrValidationError(BillmgrError):
    """Ошибка валидации данных"""

    pass


# Экспорт
__all__ = [
    "register_error_handlers",
    "BillmgrError",
    "BillmgrAuthError",
    "BillmgrAPIError",
    "BillmgrValidationError",
]
