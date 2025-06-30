# coding=utf-8


class NotImplementedRootLocaleTranslator(Exception):
    def __init__(self, root_locale) -> None:
        super().__init__(
            f"""\n
        You do not have a root locale translator.
        Root locale is "{root_locale}"
        """
        )
