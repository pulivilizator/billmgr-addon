# coding=utf-8
from typing import Iterable, Optional

from app.fluentbillmgr.src.abc import AbstractTranslator
from app.fluentbillmgr.src.abc.runner import AbstractTranslatorRunner
from app.fluentbillmgr.src.impl import AttribTracer


class TranslatorRunner(AbstractTranslatorRunner, AttribTracer):
    def __init__(self, translators: Iterable[AbstractTranslator], separator: str = "-", locale: Optional[str] = None) -> None:
        super().__init__()
        self.translators = translators
        self.separator = separator
        self.request_line = ""
        self.locale = locale

    def get(self, key: str, **kwargs) -> str:
        return self._get_translation(key, **kwargs)

    def _get_translation(self, key, **kwargs):
        for translator in self.translators:
            try:
                return translator.get(key, **kwargs)
            except KeyError:
                continue

    def __call__(self, **kwargs) -> str:
        text = self._get_translation(self.request_line[:-1], **kwargs)
        self.request_line = ""
        return text

    def __getattr__(self, item: str) -> 'TranslatorRunner':
        self.request_line += f"{item}{self.separator}"
        return self
