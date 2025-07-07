# coding=utf-8

from fluent_compiler.bundle import FluentBundle

from ..abc import AbstractTranslator


class FluentTranslator(AbstractTranslator):
    def __init__(self, locale: str, translator: FluentBundle, separator: str = "-"):
        self.locale = locale
        self.translator = translator
        self.separator = separator

    def get(self, key: str, **kwargs):
        text, errors = self.translator.format(key, kwargs)
        if errors:
            raise errors.pop()
        return text

    def __repr__(self):
        return f'<fluentogram.FluentTranslator instance, "{self.locale:}">'
