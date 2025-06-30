# coding=utf-8

from app.fluentbillmgr.src.abc import AbstractAttribTracer


class AttribTracer(AbstractAttribTracer):
    def __init__(self) -> None:
        self.request_line = ""

    def _get_request_line(self) -> str:
        request_line = self.request_line
        self.request_line = ""
        return request_line

    def __getattr__(self, item) -> 'AttribTracer':
        self.request_line += f"{item}{self.separator}"
        return self
