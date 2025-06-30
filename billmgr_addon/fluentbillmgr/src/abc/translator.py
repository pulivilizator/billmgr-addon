# coding=utf-8
from abc import ABC, abstractmethod
from typing import Any


class AbstractTranslator(ABC):
    @abstractmethod
    def __init__(self, locale: str, translator: Any, separator: str = "-") -> None:
        self.locale = locale
        self.separator = separator
        self.translator = translator

    @abstractmethod
    def get(self, key: str, **kwargs) -> str:
        raise NotImplementedError
