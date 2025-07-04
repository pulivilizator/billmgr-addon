# coding=utf-8
from abc import ABC, abstractmethod

from .misc import AbstractAttribTracer


class AbstractTranslatorRunner(AbstractAttribTracer, ABC):
    @abstractmethod
    def get(self, key: str, **kwargs) -> str: ...
    @abstractmethod
    def _get_translation(self, key, **kwargs) -> str: ...

    @abstractmethod
    def __call__(self, **kwargs) -> str: ...

    @abstractmethod
    def __getattr__(self, item: str) -> "AbstractTranslatorRunner": ...
