# -*- coding: utf-8 -*-
import ipaddress
from typing import Optional

from flask import Request
from werkzeug.datastructures import MultiDict

from ..core.i18n import get_i18n
from ..fluentbillmgr import TranslatorRunner
from ..utils.billmgr_api import BillmgrAPI


class MgrRequest:
    def __init__(self, wsgi_environ: dict):
        self.environ = wsgi_environ
        self.params = MgrRequest._parse_environ_params(self.environ)
        self._xml_input = wsgi_environ["wsgi.input"].read()
        self.user_api = None
        self.cookies = MgrRequest._parse_environ_cookies(self.environ)

    @property
    def xml_input(self):
        return self._xml_input

    @property
    def action_name(self):
        return self.environ.get("ACTION_NAME")

    @property
    def auth_user(self):
        return self.environ.get("AUTH_USER")

    @property
    def auth_level(self):
        return int(self.environ.get("AUTH_LEVEL"))

    @property
    def auth_ip(self):
        return self.environ.get("AUTH_IP")

    @property
    def lang(self):
        lang_parts = self.cookies.get("billmgrlang5").split(":")
        if len(lang_parts) > 1:
            return lang_parts[1]
        return lang_parts[0]

    @property
    def i18n(self) -> TranslatorRunner:
        return get_i18n(self.lang)

    @classmethod
    def _parse_environ_cookies(cls, environ: dict):
        cookies_string: str = environ.get("HTTP_COOKIE")
        if cookies_string is None:
            return {}

        cookies = [i.split("=", maxsplit=1) for i in cookies_string.split("; ")]
        cookies = {i[0]: i[1] for i in cookies}
        return cookies

    @classmethod
    def _parse_environ_params(cls, environ: dict):
        mgr_params = MultiDict()
        for key, value in environ.items():
            if key.startswith("PARAM_"):
                param_name = key.split("PARAM_")[1]
                mgr_params.add(param_name, value)

        return mgr_params

    def init_user_api(
        self, url, interface=None, default_remote_address=None, default_forwarded_secret=None
    ):
        ip_address_string = str(self.environ.get("HTTP_X_FORWARDED_FOR", default_remote_address))
        ip_address = ipaddress.ip_address(ip_address_string)
        billmgr_api = BillmgrAPI(
            url=url,
            interface=interface,
            session_id=self.cookies.get("billmgrses5"),
            headers={
                "X-Forwarded-For": str(ip_address),
                "X-Forwarded-Secret": self.environ.get(
                    "HTTP_X_FORWARDED_SECRET", default_forwarded_secret
                ),
            },
        )
        self.user_api = billmgr_api


class CgiRequest:
    def __init__(self, request: Request):
        self._request = request
        self.user = None
        self.query = MultiDict()
        self.body = MultiDict()
        self.form = MultiDict()

        self._fill_multidict(self.query, request.args)

        if request.method != "GET":
            if request.is_json:
                json_data = request.get_json(silent=True) or {}
                self._fill_multidict(self.body, json_data)
            else:
                self._fill_multidict(self.form, request.form)

    def _fill_multidict(self, target: MultiDict, source, transform=None) -> None:
        if hasattr(source, "lists"):
            for key, values in source.lists():
                for val in values:
                    target.add(key, transform(key, val) if transform else val)
        else:
            for key, val in source.items():
                target.add(key, transform(key, val) if transform else val)

    def get_param(self, key: str, many: bool = False):
        dicts = (self.body, self.form, self.query)

        if many:
            result = []
            for d in dicts:
                result.extend(d.getlist(key))
            return result

        for d in dicts:
            if key in d:
                return d.get(key)
        return None

    @property
    def func(self) -> Optional[str]:
        return self.get_param("func")

    @property
    def billmgr_session(self) -> Optional[str]:
        return self._request.cookies.get("billmgrses5")

    def __repr__(self) -> str:
        return (
            f"<CgiRequest method={self._request.method}, "
            f"query={dict(self.query)}, "
            f"body={dict(self.body)}, "
            f"form={dict(self.form)}>"
        )
