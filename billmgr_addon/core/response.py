# -*- coding: utf-8 -*-

import xml.etree.ElementTree as ET
from abc import ABC
from xml.etree.ElementTree import Element


class MgrResponse(ABC):
    def __init__(self) -> None:
        self.root: Element = ET.Element("doc")

    def __str__(self) -> str:
        return ET.tostring(self.root, encoding="unicode", method="xml")


class MgrOkResponse(MgrResponse):
    def __init__(self) -> None:
        super().__init__()
        ET.SubElement(self.root, "ok")


class MgrRedirectResponse(MgrResponse):
    """
    type бывает list, form, top, blank, url
    Для форм и списков еще можно задать свойство child=yes, sametab=yes, parenttab=yes управления в какой вкладке открыть
    notifyup = если нужно обновить счётчики в нотифаях
    есть еще child=drawer но я не пробовал это где-то кроме визардов

    при redirect_type=url, в func ложить сам url
    """

    def __init__(
        self, redirect_type, func, is_same_tab=None, is_child_tab=None, is_parent_tab=None
    ) -> None:
        super().__init__()
        ok_element = ET.SubElement(self.root, "ok", attrib={"type": redirect_type})
        if is_same_tab:
            ok_element["sametab"] = "yes"
        if is_child_tab:
            ok_element["child"] = "yes"
        if is_parent_tab:
            ok_element["parenttab"] = "yes"
        if redirect_type in ["blank", "url"]:
            ok_element.text = func
        else:
            ok_element.text = f"func={func}"


class MgrErrorResponse(MgrResponse):
    def __init__(self, message, exception: Exception = None) -> None:
        super().__init__()
        self._message = message
        self.exception = exception
        error_element = ET.SubElement(self.root, "error")
        error_element.attrib.update(
            {
                "type": "xml",
                "report": "no",
                "lang": "en",
                # 'code': '1'
            }
        )
        self.message_element = ET.SubElement(error_element, "msg")
        self.message_element.text = self._message

    @property
    def message(self):
        return self._message

    @message.setter
    def message(self, value):
        self._message = value
        self.message_element.text = self._message


class MgrUnknownErrorResponse(MgrErrorResponse):
    def __init__(self, exception=None) -> None:
        super().__init__("Unknown Error", exception=exception)
