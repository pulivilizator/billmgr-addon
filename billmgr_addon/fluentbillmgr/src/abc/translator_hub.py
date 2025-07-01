# coding=utf-8

from abc import ABC, abstractmethod

from app.fluentbillmgr.src.abc.runner import AbstractTranslatorRunner


class AbstractTranslatorsHub(ABC):
    @abstractmethod
    def __init__(self):
        raise NotImplementedError

    @abstractmethod
    def get_translator_by_locale(self, locale: str) -> AbstractTranslatorRunner:
        raise NotImplementedError
