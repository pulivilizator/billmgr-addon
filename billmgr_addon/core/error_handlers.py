# -*- coding: utf-8 -*-

from flask import jsonify
from werkzeug.exceptions import HTTPException, InternalServerError
from werkzeug.http import HTTP_STATUS_CODES

from billmgr_addon.utils.logging import LOGGER


def register_error_handlers(app):
    app.register_error_handler(HTTPException, handle_http_exception)
    app.register_error_handler(500, handle_internal_error)
    app.register_error_handler(Exception, handle_exception)


def success_response(payload=None):
    payload = {"status": "success", "payload": payload}
    response = jsonify(payload)
    response.status_code = 200
    return response


def error_response(status_code, message=None):
    payload = {"status": "error", "message": HTTP_STATUS_CODES.get(status_code, "Unknown error")}
    if message:
        payload["message"] = message
    response = jsonify(payload)
    response.status_code = status_code
    return response


def bad_request(message):
    return error_response(400, message)


def handle_http_exception(exception: HTTPException):
    LOGGER.info("handle_http_exception")
    return error_response(exception.code)


def handle_internal_error(exception: InternalServerError):
    LOGGER.exception(
        exception.original_exception
    )  # ".original_exception" is used when it was caused by non-explicit 500 errors.
    return error_response(exception.code)


def handle_exception(exception: Exception):
    # raise InternalServerError() from exception
    LOGGER.exception(exception)
    return error_response(500)


class BillmgrError(Exception):
    """Базовое исключение для ошибок"""

    def __init__(self, message, code=None):
        self.message = message
        self.code = code
        super().__init__(message)


class BillmgrAuthError(BillmgrError):
    """Ошибка авторизации"""

    pass


class BillmgrAPIError(BillmgrError):
    """Ошибка API"""

    pass


class BillmgrValidationError(BillmgrError):
    """Ошибка валидации данных"""

    pass


__all__ = [
    "register_error_handlers",
    "BillmgrError",
    "BillmgrAuthError",
    "BillmgrAPIError",
    "BillmgrValidationError",
]
