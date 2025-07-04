# -*- coding: utf-8 -*-

from abc import ABC, abstractmethod
import asyncio
import os
from typing import Iterable, List, Optional

from flask import Flask, Response, current_app, request
from flask_login import current_user

from ..utils.logging import LOGGER
from .request_types import CgiRequest, MgrRequest
from .response import MgrErrorResponse, MgrUnknownErrorResponse, MgrResponse
from .ui import MgrForm, MgrList, MgrUI, MgrError


class MgrRouter:
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
                mgr_request.init_user_api(current_app.config.get('BILLMGR_API_URL'),
                                        interface=current_app.config.get('BILLMGR_API_USE_INTERFACE'),
                                        default_remote_address=request.remote_addr,
                                        default_forwarded_secret=current_app.config.get('FORWARDED_SECRET'))
    
            LOGGER.debug(f"mgr_request.xml_input {mgr_request.xml_input}")
            LOGGER.debug(f"mgr_request.params {mgr_request.params}")
            LOGGER.debug(f"mgr_request.environ {mgr_request.environ}")
            return await endpoint.handle_request(mgr_request)

        cgi_request = CgiRequest(request=request)
        method = request.method
        func_name = cgi_request.func
        LOGGER.debug(f"cgi request: func - {func_name}, method - {method}, params - {repr(cgi_request)}")

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
        if (self.auth_level is None or self.auth_level == user.auth_level) and user.has_roles(self.roles_required):
            cgi_request.user = user
            return await self._handle_request(cgi_request)

        return Response("Forbidden", status=403)

    @abstractmethod
    async def _handle_request(self, cgi_request: CgiRequest):
        raise NotImplementedError


class CgiFallbackEndpoint(CgiEndpoint):
    def __init__(self):
        super().__init__(None)

    async def _handle_request(self, cgi_request: CgiRequest):
        return Response("Cgi handler not found", status=404)


class HtmlCgiEndpoint(CgiEndpoint):
    html_file_path: Optional[str] = None

    def __init__(self, function_name: str):
        super().__init__(function_name)
        if self.html_file_path is None:
            raise NotImplementedError("html_file_path must be defined in the subclass")
        
        if not os.path.exists(self.html_file_path):
            LOGGER.warning(f"HTML file specified in {self.__class__.__name__} not found at: {self.html_file_path}")
            raise FileNotFoundError(f"HTML file not found at: {self.html_file_path}")


    async def _handle_request(self, cgi_request: CgiRequest) -> Response:
        try:
            with open(self.html_file_path, 'r', encoding='utf-8') as f:
                html_content = f.read()
            billmgr_api_url = current_app.config.get('BILLMGR_API_URL')
            billmgr_api_url_parse_result = urllib.parse.urlparse(billmgr_api_url)
            billmgr_host = billmgr_api_url_parse_result.hostname
            html_content = html_content.replace("{{BILLMGR_HOST}}", billmgr_host)
            html_content = html_content.replace("{{WEBSOCKET_HOST}}", current_app.config.get('PROXY_WEBSOCKET_HOST'))
            html_content = html_content.replace("{{WEBSOCKET_PORT}}", current_app.config.get('PROXY_WEBSOCKET_PORT'))

            # TODO: Можно подключить шаблонизатор(jinja2) в будущем при необходимости
            
            return Response(html_content, mimetype='text/html')
        except FileNotFoundError:
            LOGGER.error(f"HTML file not found at {self.html_file_path}")
            return Response(f"Required HTML file not found.", status=404)
        except Exception as e:
            LOGGER.exception(f"Error reading HTML file ({self.html_file_path}): {e}")
            return Response("Internal Server Error reading HTML file", status=500)


class MgrEndpoint(ABC):
    auth_level: Optional[int] = None
    init_user_api: bool = True

    def __init__(self, action_name: str, fallback_on_error=False):
        self.name = action_name
        self.fallback_on_error = fallback_on_error

    @abstractmethod
    async def get(self, mgr_request: MgrRequest):
        return MgrErrorResponse(mgr_request.i18n.error.action_not_implemented(action_name='get', name=self.name))

    async def handle_request(self, mgr_request: MgrRequest):
        response = None
        LOGGER.debug(f"MgrEndpoint handle_request {self.__class__.auth_level} == {mgr_request.auth_level} -> {self.__class__.auth_level == mgr_request.auth_level}")
        if self.__class__.auth_level is None or self.__class__.auth_level == mgr_request.auth_level:
            response = await self._handle_request(mgr_request)
        else:
            # TODO - translate!
            response = MgrErrorResponse(f"У вас недостаточно прав на выполнение функции {self.name}")

        response = str(response)
        LOGGER.debug(response)
        return response

    async def _handle_get(self, mgr_request: MgrRequest):
        return await self.get(mgr_request)

    @staticmethod
    def _get_action_type(mgr_request: MgrRequest):
        return "get"

    def _get_action_handler(self, action_type: str):
        handler = None
        if action_type == "get":
            handler = self._handle_get
        else:
            raise ValueError(f"Can not handle unknown action type [{action_type}]")

        return handler

    async def _handle_request(self, mgr_request: MgrRequest):
        mgr_response = None
        try:
            action_type = self._get_action_type(mgr_request)
            handler = self._get_action_handler(action_type)
            if self.__class__.init_user_api:
                async with mgr_request.user_api:
                    mgr_response = await handler(mgr_request)
            else:
                mgr_response = await handler(mgr_request)

            if not isinstance(mgr_response, (MgrUI, MgrResponse)):
                raise TypeError(
                    "Endpoint handler should return MgrUI or MgrResponse instance"
                )
            elif isinstance(mgr_response, MgrUI):
                mgr_response.patch_xml()

        except MgrError as e:
            mgr_response = MgrErrorResponse(e.message)

        except Exception as e:
            LOGGER.exception(e)
            if self.fallback_on_error:
                mgr_response = mgr_request.xml_input

            mgr_response = MgrUnknownErrorResponse(exception=e)

        return mgr_response


class MgrFallbackEndpoint(MgrEndpoint):
    def __init__(self):
        super().__init__(None)

    async def get(self, mgr_request: MgrRequest):
        return mgr_request.xml_input

    async def _handle_request(self, mgr_request: MgrRequest):
        return await self.get(mgr_request)


class ActionEndpoint(MgrEndpoint):
    pass
    # TODO - return OK or Error response


class ListEndpoint(MgrEndpoint):
    use_parent_data_from_request = False

    @abstractmethod
    async def get(self, mgr_list: MgrList, mgr_request: MgrRequest):
        return MgrErrorResponse(mgr_request.i18n.error.action_not_implemented(action_name='get', name=self.name))

    async def _handle_get(self, mgr_request: MgrRequest):
        mgr_list = MgrList.from_request(mgr_request)
        if self.__class__.use_parent_data_from_request:
            mgr_list.parent_id = mgr_request.params.get("elid")
            mgr_list.parent_name = mgr_request.params.get("elname")
            mgr_list.page_number = mgr_request.params.get("p_num")
            mgr_list.on_page_count = mgr_request.params.get("p_cnt")
        # self.load_options(form, mgr_request)
        return await self.get(mgr_list, mgr_request)


class FormEndpoint(MgrEndpoint):
    use_parent_data_from_request = False

    class PresetTaskError(Exception):
        pass

    class PresetTimeoutError(Exception):
        pass

    class PresetTypeError(TypeError):
        pass

    option_presets = {}

    @classmethod
    async def _apply_option_presets(cls, form: MgrForm, mgr_request: MgrRequest):
        field_options = {}
        tasks = []
        for name, preset in cls.option_presets.items():
            if asyncio.iscoroutinefunction(preset):
                task = asyncio.create_task(preset(form, mgr_request), name=name)
                tasks.append(task)
            elif callable(preset):
                field_options[name] = preset(form, mgr_request)
            elif isinstance(preset, list):
                field_options[name] = preset
            else:
                raise FormEndpoint.PresetTypeError()

        if tasks:
            # wait until tasks are complete or task raised exception or timeout occured
            done, pending = await asyncio.wait(
                tasks, timeout=30, return_when=asyncio.FIRST_EXCEPTION
            )

            if pending:
                # cancel unfinished tasks
                for task in pending:
                    task.cancel()

                # if any task raised exception, raise error
                failed_task = next((t for t in done if t.exception() is not None), None)
                if failed_task:
                    raise FormEndpoint.PresetTaskError() from failed_task.exception()

                # raise timeout error, because some tasks left unfinished
                raise FormEndpoint.PresetTimeoutError()

            # get options from finished tasks
            for task in done:
                field_options[task.get_name()] = task.result()

        for name, options in field_options.items():
            form.set_options(name, options)

    @abstractmethod
    async def get(self, form: MgrForm, mgr_request: MgrRequest):
        return MgrErrorResponse(mgr_request.i18n.error.action_not_implemented(action_name='get', name=self.name))

    @abstractmethod
    async def setvalues(self, form: MgrForm, mgr_request: MgrRequest):
        return MgrErrorResponse(mgr_request.i18n.error.action_not_implemented(action_name='setvalues', name=self.name))

    @abstractmethod
    async def new(self, mgr_request: MgrRequest):
        return MgrErrorResponse(mgr_request.i18n.error.action_not_implemented(action_name='new', name=self.name))

    @abstractmethod
    async def edit(self, mgr_request: MgrRequest):
        return MgrErrorResponse(mgr_request.i18n.error.action_not_implemented(action_name='edit', name=self.name))

    @staticmethod
    def _get_action_type(mgr_request: MgrRequest):
        params = mgr_request.params
        if params.get("sok") == "ok":
            if params.get("elid") is None:
                return "new"

            return "edit"

        if params.get("sv_field") is not None:
            return "setvalues"

        return "get"

    def _get_action_handler(self, action_type: str):
        handler = None
        if action_type == "get":
            handler = self._handle_get
        elif action_type == "setvalues":
            handler = self._handle_setvalues
        elif action_type == "new":
            handler = self._handle_new
        elif action_type == "edit":
            handler = self._handle_edit
        else:
            raise ValueError(f"Can not handle unknown action type [{action_type}]")

        return handler

    async def _handle_get(self, mgr_request: MgrRequest):
        form: MgrForm = MgrForm.from_request(mgr_request)
        if self.__class__.use_parent_data_from_request:
            form.parent_id = mgr_request.params.get("elid")
            form.parent_name = mgr_request.params.get("elname")

        if form.title_tag is not None and form.parent_name is not None:
            form.set_data_value(form.title_tag, form.parent_name)

        await self.__class__._apply_option_presets(form, mgr_request)
        return await self.get(form, mgr_request)

    async def _handle_setvalues(self, mgr_request):  # has sv_field=*****
        form:MgrForm = MgrForm.from_request(mgr_request)
        form.set_data({**mgr_request.params})
        if self.__class__.use_parent_data_from_request:
            form.parent_id = mgr_request.params.get("elid")
            form.parent_name = mgr_request.params.get("elname")

        form.updated_field = mgr_request.params.get("sv_field")

        await self.__class__._apply_option_presets(form, mgr_request)
        return await self.setvalues(form, mgr_request)

    async def _handle_new(self, mgr_request):  # has sok=ok
        return await self.new(mgr_request)

    async def _handle_edit(self, mgr_request):  # has sok=ok, has elid
        return await self.edit(mgr_request)


class ReportEndpoint(FormEndpoint):
    pass


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
