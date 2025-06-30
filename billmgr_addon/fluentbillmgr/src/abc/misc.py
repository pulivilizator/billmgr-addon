# coding=utf-8

from abc import ABC, abstractmethod


class AbstractAttribTracer(ABC):
    @abstractmethod
    def __init__(self) -> None:
        self.request_line = ""

    @abstractmethod
    def _get_request_line(self) -> str:
        request_line = self.request_line
        self.request_line = ""
        return request_line

    @abstractmethod
    def __getattr__(self, item) -> 'AbstractAttribTracer':
        self.request_line += f"{item}{self.separator}"
        return self
