# -*- coding: utf-8 -*-

import xml.etree.ElementTree as ET
from typing import Any, Dict, List, Optional

from .response import MgrResponse


class MgrUI:
    """Базовый класс для UI компонентов BILLmanager"""

    def __init__(self):
        self.root = ET.Element("doc")

    def to_xml(self) -> str:
        """Преобразование в XML строку"""
        return ET.tostring(self.root, encoding="unicode")

    def to_response(self) -> MgrResponse:
        """Преобразование в MGR ответ"""
        return MgrResponse(self.to_xml())


class MgrForm(MgrUI):
    """
    Компонент для создания форм BILLmanager

    Позволяет добавлять поля, кнопки и другие элементы формы.
    """

    def __init__(self):
        super().__init__()
        self.form_elem = ET.SubElement(self.root, "form")
        self.fields = {}

    def add_field(self, name: str, field_type: str = "text", **kwargs):
        """Добавить поле формы"""
        field_elem = ET.SubElement(self.form_elem, "field")
        field_elem.set("name", name)
        field_elem.set("type", field_type)

        # Добавление дополнительных атрибутов
        for key, value in kwargs.items():
            if value is not None:
                field_elem.set(key, str(value))

        self.fields[name] = field_elem
        return field_elem

    def add_text_field(
        self, name: str, label: str = None, value: str = None, required: bool = False
    ):
        """Добавить текстовое поле"""
        return self.add_field(
            name=name,
            field_type="text",
            label=label,
            value=value,
            required="yes" if required else None,
        )

    def add_password_field(self, name: str, label: str = None, required: bool = False):
        """Добавить поле пароля"""
        return self.add_field(
            name=name, field_type="password", label=label, required="yes" if required else None
        )

    def add_select_field(
        self, name: str, options: List[Dict], label: str = None, value: str = None
    ):
        """Добавить поле выбора"""
        field_elem = self.add_field(name=name, field_type="select", label=label, value=value)

        for option in options:
            option_elem = ET.SubElement(field_elem, "option")
            option_elem.set("value", str(option.get("value", "")))
            option_elem.text = str(option.get("text", ""))

        return field_elem

    def add_checkbox_field(self, name: str, label: str = None, checked: bool = False):
        """Добавить чекбокс"""
        return self.add_field(
            name=name, field_type="checkbox", label=label, checked="yes" if checked else None
        )

    def add_button(self, name: str, label: str, action: str = None):
        """Добавить кнопку"""
        button_elem = ET.SubElement(self.form_elem, "button")
        button_elem.set("name", name)
        button_elem.set("label", label)
        if action:
            button_elem.set("action", action)
        return button_elem

    def set_parent_id_from_request(self, mgr_request):
        """Установить parent_id из запроса"""
        parent_id = mgr_request.get_param("parent_id")
        if parent_id:
            self.form_elem.set("parent_id", parent_id)


class MgrList(MgrUI):
    """
    Компонент для создания списков BILLmanager

    Позволяет выводить табличные данные с заголовками и строками.
    """

    def __init__(self):
        super().__init__()
        self.list_elem = ET.SubElement(self.root, "list")
        self.headers = []
        self.rows = []

    def add_header(self, name: str, title: str, width: str = None, sort: bool = False):
        """Добавить заголовок столбца"""
        header_elem = ET.SubElement(self.list_elem, "header")
        header_elem.set("name", name)
        header_elem.set("title", title)

        if width:
            header_elem.set("width", width)
        if sort:
            header_elem.set("sort", "yes")

        self.headers.append(header_elem)
        return header_elem

    def add_row(self, data: Dict[str, Any], row_id: str = None):
        """Добавить строку данных"""
        row_elem = ET.SubElement(self.list_elem, "row")

        if row_id:
            row_elem.set("id", str(row_id))

        for key, value in data.items():
            col_elem = ET.SubElement(row_elem, "col")
            col_elem.set("name", key)
            col_elem.text = str(value) if value is not None else ""

        self.rows.append(row_elem)
        return row_elem

    def set_data_rows(self, data_list: List[Dict[str, Any]]):
        """Установить все строки данных сразу"""
        for i, data in enumerate(data_list):
            row_id = data.get("id", i)
            self.add_row(data, row_id)

    def add_action_button(self, name: str, title: str, action: str):
        """Добавить кнопку действия"""
        action_elem = ET.SubElement(self.list_elem, "action")
        action_elem.set("name", name)
        action_elem.set("title", title)
        action_elem.set("action", action)
        return action_elem

    def set_parent_id_from_request(self, mgr_request):
        """Установить parent_id из запроса"""
        parent_id = mgr_request.get_param("parent_id")
        if parent_id:
            self.list_elem.set("parent_id", parent_id)


class MgrError(MgrUI):
    """
    Компонент для отображения ошибок
    """

    def __init__(self, message: str, code: Optional[str] = None):
        super().__init__()
        error_elem = ET.SubElement(self.root, "error")
        error_elem.text = message

        if code:
            error_elem.set("code", code)


__all__ = ["MgrUI", "MgrForm", "MgrList", "MgrError"]
