# -*- coding: utf-8 -*-

from abc import ABC, abstractmethod
from typing import Iterable, List, Optional

from flask import Flask, Response, current_app, request
from flask_login import current_user

from ..utils.logging import LOGGER
from .request_types import CgiRequest, MgrRequest
from .response import MgrErrorResponse, MgrUnknownErrorResponse
from .ui import MgrForm, MgrList


class MgrRouter:
    """
    Основная система маршрутизации для плагинов
    """

    def __init__(self, app: Flask, endpoints: List["Endpoint"]):
        self.app = app
        LOGGER.debug("######## MgrRouter __init__")
        app.add_url_rule("/", view_func=self.main_handler, methods=["GET", "POST"])

        self.addon_endpoints = {}
        self.cgi_endpoints = {}
        self.setup_endpoints(endpoints)

    def setup_endpoints(self, endpoints: List["Endpoint"]):
        for endpoint in endpoints:
            if isinstance(endpoint, MgrEndpoint):
                mgr_action_name = endpoint.name
                if mgr_action_name in self.addon_endpoints:
                    LOGGER.error(f"Endpoint {mgr_action_name} already exists")
                    raise Exception(f"Duplicated endpoint {mgr_action_name}")

                self.addon_endpoints[mgr_action_name] = endpoint
            elif isinstance(endpoint, CgiEndpoint):
                mgr_action_name = endpoint.name
                if mgr_action_name in self.cgi_endpoints:
                    LOGGER.error(f"Endpoint {mgr_action_name} already exists")
                    raise Exception(f"Duplicated endpoint {mgr_action_name}")

                self.cgi_endpoints[mgr_action_name] = endpoint

    async def main_handler(self, *args, **kwargs):
        event_type = request.environ.get("EVENT_TYPE")
        if event_type in ["action", "before", "after", "final"]:
            mgr_action_name = request.environ.get("ACTION_NAME")

            endpoint = self.addon_endpoints.get(mgr_action_name)
            if endpoint is None:
                endpoint = MgrFallbackEndpoint()
                LOGGER.error(f"Addon endpoint for func={mgr_action_name} is not found")

            mgr_request = MgrRequest(request.environ)
            LOGGER.debug(f"request.remote_addr  {request.remote_addr}")

            if endpoint.__class__.init_user_api:
                mgr_request.init_user_api(
                    current_app.config.get("BILLMGR_API_URL"),
                    interface=current_app.config.get("BILLMGR_API_USE_INTERFACE"),
                    default_remote_address=request.remote_addr,
                    default_forwarded_secret=current_app.config.get("FORWARDED_SECRET"),
                )

            LOGGER.debug(f"mgr_request.xml_input {mgr_request.xml_input}")
            LOGGER.debug(f"mgr_request.params {mgr_request.params}")
            LOGGER.debug(f"mgr_request.environ {mgr_request.environ}")
            return await endpoint.handle_request(mgr_request)

        cgi_request = CgiRequest(request=request)
        method = request.method
        func_name = cgi_request.func
        LOGGER.debug(
            f"cgi request: func - {func_name}, method - {method}, params - {repr(cgi_request)}"
        )

        if func_name:
            endpoint = self.cgi_endpoints.get(func_name, CgiFallbackEndpoint())
            return await endpoint.handle_request(cgi_request)

        return current_app.send_static_file("index.html")


class Endpoint(ABC):
    def __init__(self, name: str):
        self.name = name

    @abstractmethod
    async def _handle_request(self):
        raise NotImplementedError


class CgiEndpoint(ABC):
    auth_level: Optional[int] = None
    roles_required: Optional[Iterable] = None

    def __init__(self, function_name: str):
        self.name = function_name

    async def handle_request(self, cgi_request: CgiRequest) -> Response:
        user = current_user
        if (self.auth_level is None or self.auth_level == user.auth_level) and user.has_roles(
            self.roles_required
        ):
            cgi_request.user = user
            return await self._handle_request(cgi_request)

        return Response("Forbidden", status=403)

    @abstractmethod
    async def _handle_request(self, cgi_request: CgiRequest):
        raise NotImplementedError


class CgiFallbackEndpoint(CgiEndpoint):
    """Fallback эндпоинт для неизвестных CGI запросов"""

    def __init__(self):
        super().__init__("")

    async def _handle_request(self, cgi_request: CgiRequest):
        return Response("Cgi handler not found", status=404)


class MgrEndpoint(ABC):
    auth_level: Optional[int] = None
    init_user_api: bool = True

    def __init__(self, action_name: str, fallback_on_error=False):
        self.name = action_name
        self.fallback_on_error = fallback_on_error

    @abstractmethod
    async def get(self, mgr_request: MgrRequest):
        return MgrErrorResponse("Action not implemented")

    async def handle_request(self, mgr_request: MgrRequest):
        if self.__class__.auth_level is None or self.__class__.auth_level == mgr_request.auth_level:
            try:
                return await self._handle_request(mgr_request)
            except Exception as e:
                LOGGER.exception(f"Error in {self.__class__.__name__}: {e}")
                if self.fallback_on_error:
                    return MgrFallbackEndpoint().handle_request(mgr_request)
                return MgrUnknownErrorResponse()
        else:
            return MgrErrorResponse("Access denied")

    async def _handle_request(self, mgr_request: MgrRequest):
        action_type = self._get_action_type(mgr_request)
        action_handler = self._get_action_handler(action_type)

        if action_handler:
            return await action_handler(mgr_request)
        else:
            return await self._handle_get(mgr_request)

    async def _handle_get(self, mgr_request: MgrRequest):
        return await self.get(mgr_request)

    @staticmethod
    def _get_action_type(mgr_request: MgrRequest):
        return mgr_request.params.get("action", "get")

    def _get_action_handler(self, action_type: str):
        handler_map = {
            "get": self._handle_get,
        }
        return handler_map.get(action_type)


class MgrFallbackEndpoint(MgrEndpoint):
    def __init__(self):
        super().__init__("")

    async def get(self, mgr_request: MgrRequest):
        return MgrErrorResponse("Handler not found")


class ActionEndpoint(MgrEndpoint):
    pass


class ListEndpoint(MgrEndpoint):
    use_parent_data_from_request = False

    @abstractmethod
    async def get(self, mgr_list: MgrList, mgr_request: MgrRequest):
        raise NotImplementedError

    async def _handle_get(self, mgr_request: MgrRequest):
        mgr_list = MgrList()
        if self.use_parent_data_from_request:
            mgr_list.set_parent_id_from_request(mgr_request)
        return await self.get(mgr_list, mgr_request)


class FormEndpoint(MgrEndpoint):
    use_parent_data_from_request = False

    @abstractmethod
    async def get(self, form: MgrForm, mgr_request: MgrRequest):
        raise NotImplementedError

    @abstractmethod
    async def setvalues(self, form: MgrForm, mgr_request: MgrRequest):
        raise NotImplementedError

    async def new(self, mgr_request: MgrRequest):
        return MgrErrorResponse("New action not implemented")

    async def edit(self, mgr_request: MgrRequest):
        return MgrErrorResponse("Edit action not implemented")

    @staticmethod
    def _get_action_type(mgr_request: MgrRequest):
        if "setvalues" in mgr_request.params:
            return "setvalues"
        elif "sok" in mgr_request.params and "elid" in mgr_request.params:
            return "edit"
        elif "sok" in mgr_request.params:
            return "new"
        else:
            return "get"

    def _get_action_handler(self, action_type: str):
        handler_map = {
            "get": self._handle_get,
            "setvalues": self._handle_setvalues,
            "new": self._handle_new,
            "edit": self._handle_edit,
        }
        return handler_map.get(action_type)

    async def _handle_get(self, mgr_request: MgrRequest):
        form = MgrForm()
        if self.use_parent_data_from_request:
            form.set_parent_id_from_request(mgr_request)
        return await self.get(form, mgr_request)

    async def _handle_setvalues(self, mgr_request):
        form = MgrForm()
        return await self.setvalues(form, mgr_request)

    async def _handle_new(self, mgr_request):
        return await self.new(mgr_request)

    async def _handle_edit(self, mgr_request):
        return await self.edit(mgr_request)


__all__ = [
    "MgrRouter",
    "Endpoint",
    "CgiEndpoint",
    "MgrEndpoint",
    "ActionEndpoint",
    "ListEndpoint",
    "FormEndpoint",
    "CgiFallbackEndpoint",
    "MgrFallbackEndpoint",
]
