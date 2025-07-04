# coding=utf-8
from typing import Dict, Iterable, List, Union

from ....exceptions import NotImplementedRootLocaleTranslator
from ...abc import AbstractTranslator, AbstractTranslatorsHub
from ...impl import TranslatorRunner


class TranslatorHub(AbstractTranslatorsHub):
    def __init__(
        self,
        locales_map: Dict[str, Union[str, Iterable[str]]],
        translators: List[AbstractTranslator],
        root_locale: str = "en",
        separator: str = "-",
    ) -> None:
        self.locales_map = dict(
            zip(
                locales_map.keys(),
                map(
                    lambda lang: tuple([lang]) if isinstance(lang, str) else lang,
                    locales_map.values(),
                ),
            )
        )
        self.translators = translators
        self.root_locale = root_locale
        self.separator = separator
        self.storage: Dict[str, AbstractTranslator] = dict(
            zip([translator.locale for translator in translators], translators)
        )
        if not self.storage.get(root_locale):
            raise NotImplementedRootLocaleTranslator(self.root_locale)
        self.translators_map: Dict[str, Iterable[AbstractTranslator]] = self._locales_map_parser(
            self.locales_map
        )

    def _locales_map_parser(
        self, locales_map: Dict[str, Union[str, Iterable[str]]]
    ) -> Dict[str, Iterable[AbstractTranslator]]:
        return {
            lang: tuple(
                [
                    self.storage.get(locale)
                    for locale in translator_locales
                    if locale in self.storage.keys()
                ]
            )
            for lang, translator_locales in locales_map.items()
        }

    def get_translator_by_locale(self, locale: str) -> TranslatorRunner:
        translator = self.translators_map.get(locale)
        if translator is None:
            locale = self.root_locale
            translator = self.translators_map[self.root_locale]
        return TranslatorRunner(translators=translator, separator=self.separator, locale=locale)
