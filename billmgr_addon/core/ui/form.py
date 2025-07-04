# -*- coding: utf-8 -*-

import re
import xml.etree.ElementTree as ET
from abc import ABC, abstractmethod
from dataclasses import dataclass
from decimal import Decimal
from enum import Enum
from typing import List, NamedTuple, Optional, Union
from uuid import UUID
from xml.etree.ElementTree import Element

from .ui import MgrUI, MgrUnknownNode


class UuidOptionValueError(ValueError):
    def __init__(self, name, value):
        self.name = name
        self.value = value


class MgrForm(MgrUI):
    null_option_key = "null"
    # title = MgrNodeAttribute('text', default='')
    # attributes = {
    #     'nonext': '???',
    #     'clear': '???',
    #     'title': 'text', # parent_title
    #     'autocomplete': 'on/off',
    #     'cancelrefresh': 'yes/no',
    #     'nosubmit': 'yes/no',
    #     'nocancel': 'yes/no',
    #     'noback': 'yes/no',
    #     'progress': 'yes/notime/wait',
    #     'action': 'text',
    #     'helpurl': 'text',
    # }

    @classmethod
    def get_null_option(cls):
        return {"key": cls.null_option_key}

    @dataclass
    class OptionRow:
        key: str
        label: Optional[str]
        original_value: Optional[str]

    def _init_ui_objects(self):
        form_element = self.metadata_element.find("form")
        buttons_element = self.metadata_element.find("buttons")
        self.title_tag = form_element.get("title")
        self.has_submit_button = form_element.get("nosubmit", "no") == "no"
        self.has_cancel_button = form_element.get("nocancel", "no") == "no"
        self.has_back_button = form_element.get("noback", "no") == "no"
        self.buttons = None

        page_elements = form_element.findall("page")
        if page_elements:
            self.pages = {
                el.attrib["name"]: MgrFormPage.from_element(el, form=self) for el in page_elements
            }
        else:
            hidden_page_element = Element("page")
            form_group_elements = list(form_element)
            for form_group_element in form_group_elements:
                hidden_page_element.append(form_group_element)
            self.pages = {None: MgrFormPage.from_element(hidden_page_element, form=self)}

        if buttons_element:
            button_elements = buttons_element.findall("button")
            self.buttons = {
                el.attrib["name"]: MgrFormButton.from_element(el, form=self)
                for el in button_elements
            }

    def _init_data(self):
        # self.params = {}
        self.field_data = {}
        self.field_options = {}

        # self.parent_id = self._get_root_child_element_text("plid")
        # self.parent_name = self._get_root_child_element_text('plname')
        self.parent_id = None
        self.parent_name = None
        self.updated_field = None

        for element in self.root:
            if element.tag == "slist":
                list_name = element.get("name")
                self.field_options[list_name] = []
                for option_element in list(element):
                    if option_element.tag == "val":
                        key = option_element.get("key")
                        label = option_element.text
                        self.field_options[list_name].append({"key": key, "label": label})
                    elif option_element.tag == "msg":
                        key = option_element.text
                        self.field_options[list_name].append({"key": key})

            if element.tag == "list":
                list_name = element.get("name")
                list_field: MgrListData = self.get_field(list_name)
                self.field_data[list_name] = []
                row_elements = element.findall("elem")
                for row_element in row_elements:
                    data_row = {}
                    for column_value_element in list(row_element):
                        column_name = column_value_element.tag
                        # TODO - parse 'price' and 'action' elements properly
                        column: MgrListData.Column = list_field.columns[column_name]
                        column_value = column.__class__.get_value_from_element(column_value_element)
                        # data_row[column_name] = column_value_element.text
                        data_row[column_name] = column_value

                    self.field_data[list_name].append(data_row)

            # elif element.tag not in [self.title_tag, "metadata", "messages", "doc"]:
            elif element.tag not in ["metadata", "messages", "doc"]:
                name = element.tag
                self.field_data[name] = element.text

    def set_data(self, data: dict):
        self.field_data = {**data}

    def set_data_value(self, name, value):
        self.field_data[name] = value

    def get_data_value(self, name):
        return self.field_data.get(name)

    @staticmethod
    def get_uuid_option_value(field_name, option_value):
        # option_value = self.get_data_value(field_name)
        if option_value is None or option_value == MgrForm.null_option_key:
            return None
        else:
            try:
                return str(UUID(option_value))
            except:
                raise UuidOptionValueError(field_name, option_value)

    # def get_uuid_option_value(self, field_name):
    #     option_value = self.get_data_value(field_name)
    #     if option_value is None or option_value == MgrForm.null_option_key:
    #         return None
    #     else:
    #         try:
    #             return str(UUID(option_value))
    #         except:
    #             raise UuidOptionValueError(field_name, option_value)

    def get_options(self, name: str):
        return self.field_options.get(name)

    def set_options(
        self, name: str, options: list, key_name="key", label_name="label", keys_as_labels=False
    ):
        self.field_options[name] = []
        for option in options:
            NO_ORIGINAL_VALUE = object()
            NO_LABEL = object()
            option_key, option_label, original_value = None, None, NO_ORIGINAL_VALUE
            # TODO - add OptionRow case
            if isinstance(option, dict):
                option_key = option[key_name]
                option_label = option.get(label_name, NO_LABEL)
                original_value = option.get("original_value", NO_ORIGINAL_VALUE)
            else:
                option_key = option
                option_label = NO_LABEL

            if option_key is None:
                option_key = self.__class__.null_option_key

            if keys_as_labels:
                option_label = option_key

            new_row = None
            if option_label == NO_LABEL:
                new_row = {"key": str(option_key)}
            else:
                new_row = {"key": str(option_key), "label": str(option_label)}
                if original_value != NO_ORIGINAL_VALUE:
                    new_row["original_value"] = original_value

            self.field_options[name].append(new_row)

    def get_field(self, name: str) -> "MgrField":
        field = None
        for page_name, page in self.pages.items():
            field = page.get_field(name)
            if field:
                break

        return field

    def remove_field(self, name: str) -> "MgrField":
        for page_name, page in self.pages.items():
            page.remove_field(name)
            break

    def get_message(self, name: str) -> str:
        return self.messages.get(name)

    def set_message(self, name: str, value: str):
        self.messages[name] = value

    def add_button(self, button_type, name, attributes: dict = None):
        if self.buttons is None:
            self.buttons = {}

        button = MgrFormButton(button_type, name, form=self, attributes=attributes)
        self.buttons[button.name] = button
        return button

    def patch_xml(self):
        form_attributes = {
            # "title": self.title_tag,
            # "nosubmit": "no" if self.has_submit_button else "yes",
            # "nocancel": "no" if self.has_cancel_button else "yes",
            # "noback": "no" if self.has_back_button else "yes",
        }
        if self.title_tag is not None:
            form_attributes["title"] = self.title_tag

        form_element = ET.SubElement(
            self.metadata_element,
            "form",
            attrib=form_attributes,
        )

        if self.buttons is None:
            if not self.has_submit_button:
                form_element.set("nosubmit", "yes")
            if not self.has_cancel_button:
                form_element.set("nocancel", "yes")
            if not self.has_back_button:
                form_element.set("noback", "yes")
        else:
            buttons_element = ET.SubElement(self.metadata_element, "buttons")
            for name, button in self.buttons.items():
                buttons_element.append(button.to_xml())

        for name, page in self.pages.items():
            if name is None:
                for form_group_element in list(page.to_xml()):
                    form_element.append(form_group_element)
            else:
                form_element.append(page.to_xml())

        for name, message in self.messages.items():
            ET.SubElement(self.messages_element, "msg", attrib={"name": name}).text = str(message)

        for name, value in self.field_data.items():
            if isinstance(value, list):
                list_element = ET.SubElement(self.root, "list", attrib={"name": name})
                for data_row in value:
                    row_element = ET.SubElement(list_element, "elem")
                    for column_name, column_value in data_row.items():
                        if isinstance(column_value, MgrListData.ColumnValue):
                            column_value_element = column_value.to_xml()
                            row_element.append(column_value_element)
                            # price_element = ET.SubElement(row_element, "price")
                        else:
                            ET.SubElement(row_element, column_name).text = column_value
            else:
                ET.SubElement(self.root, name).text = str(value)

        for key, options in self.field_options.items():
            list_element = ET.SubElement(self.root, "slist", attrib={"name": key})
            for option in options:
                option_key = option["key"]
                option_element = None
                if "label" in option:
                    option_element = Element("val", attrib={"key": option_key})
                    option_element.text = str(option["label"])
                else:
                    option_element = Element("msg")
                    option_element.text = option_key

                list_element.append(option_element)

    @property
    def parent_id(self):
        # return self.params.get('elid')
        # return self.get_data_value("elid")
        return self._parent_id

    @parent_id.setter
    def parent_id(self, value):
        # self.params['elid'] = value
        # self.set_data_value("elid", value)
        self._parent_id = value

    @property
    def parent_name(self):
        # return self.get_data_value("elname")
        return self._parent_name

    @parent_name.setter
    def parent_name(self, value):
        # self.set_data_value("elname", value)
        self._parent_name = value

    @property
    def title_tag(self):
        return self._title_tag

    @title_tag.setter
    def title_tag(self, value):
        self._title_tag = value

    @property
    def title(self):
        # return self.params.get(self.title_tag)
        return self.get_data_value(self.title_tag)

    @title.setter
    def title(self, value):
        # # TODO - also change tag value?
        # self.params[self.title_tag] = value
        self.set_data_value(self.title_tag, value)

    # @property
    # def values(self):
    #     pass

    # def set_values(self, values):
    #     pass


# <page>
class MgrFormPage:
    def __init__(
        self,
        name,
        form: MgrForm = None,
        form_groups: dict = None,
        attributes: dict = None,
    ) -> None:
        self.name = name
        self.form = form
        self.form_groups = {}
        if form_groups:
            self.form_groups = form_groups

        self.attributes = {}
        if attributes:
            self.attributes = {**attributes}

    @classmethod
    def from_element(cls, page_element: Element, form: MgrForm = None):
        name = page_element.get("name")
        form_group_elements = list(page_element)
        form_groups = {
            el.attrib["name"]: MgrFormGroup.from_element(el, form=form)
            for el in form_group_elements
        }
        instance = cls(name, form=form, form_groups=form_groups, attributes=page_element.attrib)
        return instance

    def to_xml(self):
        attributes = {**self.attributes}
        attributes["name"] = self.name
        page_element = Element("page", attrib=attributes)
        for name, form_group in self.form_groups.items():
            page_element.append(form_group.to_xml())
        return page_element

    def get_field(self, name: str) -> "MgrField":
        field = None
        for group_name, group in self.form_groups.items():
            field = group.get_field(name)
            if field:
                break

        return field

    def remove_field(self, name: str) -> "MgrField":
        for name, group in self.form_groups.items():
            field = group.get_field(name)
            if field:
                group.remove_field(name)
                break


# <field>
class MgrFormGroup:
    element_name = "field"

    def __init__(
        self, name, form: MgrForm = None, fields: dict = None, attributes: dict = None
    ) -> None:
        self.name = name
        self.form = form
        self.fields = {}
        if fields:
            self.fields = fields

        self.attributes = {}
        if attributes:
            self.attributes = {**attributes}

    @classmethod
    def from_element(cls, form_group_element: Element, form: MgrForm = None):
        name = form_group_element.get("name")
        field_elements = list(form_group_element)
        # form_groups = {el['name']:MgrFormGroup.from_element(el, form=form) for el in field_elements}
        fields = {}
        for field_element in field_elements:
            field = cls.get_form_field_from_element(field_element, form=form)
            if field is None:
                field = MgrUnknownNode.from_element(field_element)

            fields[field.name] = field

        instance = cls(name, form=form, fields=fields, attributes=form_group_element.attrib)
        return instance

    @classmethod
    def get_form_field_from_element(cls, field_element: Element, form: MgrForm = None):
        field = None
        if field_element.tag == "list":
            field = MgrListData.from_element(field_element, form=form)
        elif field_element.tag == "textdata":
            field = MgrTextData.from_element(field_element, form=form)
        elif field_element.tag == "textarea":
            field = MgrTextArea.from_element(field_element, form=form)
        elif field_element.tag == "select":
            field = MgrSelect.from_element(field_element, form=form)
        elif field_element.tag == "slider":
            field = MgrSlider.from_element(field_element, form=form)
        elif field_element.tag == "input":
            input_type = field_element.get("type")
            if input_type == "text":
                field = MgrText.from_element(field_element, form=form)
            elif input_type == "checkbox":
                field = MgrCheckbox.from_element(field_element, form=form)
            elif input_type == "password":
                field = MgrPassword.from_element(field_element, form=form)
            elif input_type == "hidden":
                field = MgrHidden.from_element(field_element, form=form)

        elif field_element.tag == "button":
            field = MgrFormButton.from_element(field_element, form=form)

        return field

    def to_xml(self):
        attributes = {**self.attributes}
        attributes["name"] = self.name
        form_group_element = Element(self.__class__.element_name, attrib=attributes)
        for name, field in self.fields.items():
            form_group_element.append(field.to_xml())
        return form_group_element

    def get_field(self, name: str) -> "MgrField":
        return self.fields.get(name)

    def add_field(self, field: "MgrField"):
        self.fields[field.name] = field

    def remove_field(self, field: "MgrField"):
        del self.fields[field.name]


class MgrFormButtonsGroup(MgrFormGroup):
    element_name = "buttons"

    @classmethod
    def get_form_field_from_element(cls, field_element: Element, form: MgrForm = None):
        field = None
        if field_element.tag == "button":
            field = MgrFormButton.from_element(field_element, form=form)

        return field

    def get_field(self, name: str) -> "MgrFormButton":
        return self.fields.get(name)

    def add_field(self, button: "MgrFormButton"):
        self.fields[button.name] = button

    def get_button(self, name: str) -> "MgrFormButton":
        return self.fields.get(name)

    def add_button(self, button: "MgrFormButton"):
        self.fields[button.name] = button


# <input>, <select>, etc
class MgrField:
    def __init__(self, name, form: MgrForm = None, attributes: dict = None) -> None:
        self.form = form
        self.attributes = {}
        if attributes:
            self.attributes = {**attributes}

        self.name = name

    @classmethod
    def from_element(cls, field_element: Element, form: MgrForm = None):
        name = field_element.get("name")
        instance = cls(name, form=form, attributes=field_element.attrib)
        return instance

    @property
    def name(self):
        return self.attributes.get("name")

    @name.setter
    def name(self, value: str):
        self.attributes["name"] = value

    def get_label(self) -> str:
        return self.form.get_message(self.name)

    def set_label(self, value: str):
        return self.form.set_message(self.name, value)

    # TODO - get/set hints

    # def __init__(self, name=None, level=None) -> None:
    #     super().__init__(name, level)
    #     self.value = None

    # def to_xml_element(self) -> Element:
    #     pass
    # return super().to_xml_element()


# <button>
class MgrFormButton(MgrField):
    def __init__(self, button_type, name, form: MgrForm = None, attributes: dict = None):
        super().__init__(name, form=form, attributes=attributes)
        self.button_type = button_type

    @classmethod
    def from_element(cls, button_element: Element, form: MgrForm = None):
        button_type = button_element.get("type")
        name = button_element.get("name")
        instance = cls(button_type, name, form=form, attributes=button_element.attrib)
        return instance

    def to_xml(self):
        attributes = {**self.attributes}
        attributes["name"] = self.name
        attributes["type"] = self.button_type
        return Element("button", attrib=attributes)


class MgrInputField(MgrField):
    input_type = "input"

    class Condition:
        def __init__(
            self,
            condition_type: str,
            hide_field: str = None,
            value: str = None,
            shadow: bool = None,
            empty: bool = None,
            form: MgrForm = None,
        ):
            """
            condition_type: (if, else)
            hide_field: field to hide when condition met
            """
            self.form = form
            self.condition_type = condition_type
            self.value = value
            self.hide_field = hide_field
            self.shadow = shadow
            self.empty = empty

        @classmethod
        def from_element(cls, field_element: Element, form: MgrForm = None):
            condition_type = field_element.tag
            value = field_element.get("value")
            hide_field = field_element.get("hide")
            shadow = field_element.get("shadow") is not None
            empty = field_element.get("empty") is not None
            return cls(
                condition_type,
                hide_field=hide_field,
                value=value,
                shadow=shadow,
                empty=empty,
                form=form,
            )

        def to_xml(self):
            attributes = {}
            if self.hide_field:
                attributes["hide"] = self.hide_field
            if self.value:
                attributes["value"] = self.value
            if self.shadow:
                attributes["shadow"] = "yes"
            if self.empty:
                attributes["empty"] = None

            return Element(self.condition_type, attrib=attributes)

    def __init__(
        self,
        name,
        is_required: bool = None,
        form: MgrForm = None,
        attributes: dict = None,
        conditions: List[Condition] = None,
    ) -> None:
        super().__init__(name, form, attributes)
        if is_required is not None:
            self.is_required = is_required
        elif self.is_required is None:
            self.is_required = False

        self.conditions = []
        if conditions is not None:
            self.conditions = conditions

    @classmethod
    def from_element(cls, field_element: Element, form: MgrForm = None):
        name = field_element.get("name")
        is_required = field_element.get("required") == "yes"

        conditions = []
        condition_elements = list(field_element)
        for condition_element in condition_elements:
            condition = cls.Condition.from_element(condition_element, form=form)
            conditions.append(condition)

        instance = cls(
            name,
            is_required=is_required,
            form=form,
            attributes=field_element.attrib,
            conditions=conditions,
        )
        return instance

    @property
    def is_required(self):
        return self.attributes.get("required") == "yes"

    @is_required.setter
    def is_required(self, value: bool):
        self.attributes["required"] = "yes" if value else "no"

    def to_xml(self):
        attributes = {**self.attributes}
        field_element = Element(self.__class__.input_type, attrib=attributes)
        for condition in self.conditions:
            condition_element = condition.to_xml()
            field_element.append(condition_element)

        return field_element


class MgrOutputField(MgrField):
    pass


class MgrText(MgrInputField):
    pass


class MgrCheckbox(MgrInputField):
    pass


class MgrPassword(MgrInputField):
    pass


class MgrHidden(MgrInputField):
    pass


class MgrSelect(MgrInputField):
    input_type = "select"


class MgrSlider(MgrInputField):
    input_type = "slider"


class MgrTextArea(MgrInputField):
    input_type = "textarea"


class MgrTextData(MgrOutputField):
    def to_xml(self):
        attributes = {**self.attributes}
        return Element("textdata", attrib=attributes)


class ColumnTypes(str, Enum):
    DATA = "data"
    MESSAGE = "msg"
    IMAGE = "img"
    PRICE = "price"
    BUTTON = "button"
    CONTROL = "control"


class ColumnAlignTypes(str, Enum):
    CENTER = "center"
    LEFT = "left"
    RIGHT = "right"


class TextWeights(str, Enum):
    NORMAL = "normal"
    BOLD = "bold"


class TextSizes(str, Enum):
    H1 = "h1"
    H2 = "h2"
    H3 = "h3"
    H4 = "h4"
    H5 = "h5"
    H6 = "h6"


class MgrListData(MgrOutputField):
    class Style(NamedTuple):
        align: ColumnAlignTypes = None
        width: str = None
        height: str = None
        weight: Union[TextWeights, str, int] = None
        size: TextSizes = None
        color: str = None

    class StylableNode:
        def __init__(self, style: "MgrListData.Style" = None, attributes: dict = None):
            self.attributes = {}
            if attributes:
                self.attributes = {**attributes}

            if style:
                # TODO - attrbutes can only be strings!
                if style.align is not None and any(
                    t.value == style.align for t in ColumnAlignTypes
                ):
                    self.align = style.align

                dimension_pattern = r"^\d+px|\d+\%$"
                if style.width is not None:
                    if not re.match(dimension_pattern, style.width):
                        raise ValueError(
                            "'width' param must be integer number with units, e.g. 10px, 50%"
                        )
                    self.width = style.width

                if style.height is not None and re.match(dimension_pattern, style.height):
                    if not re.match(dimension_pattern, style.height):
                        raise ValueError(
                            "'height' param must be integer number with units, e.g. 10px, 50%"
                        )
                    self.height = style.height

                if style.weight is not None:
                    # TODO - check if weight actually works. It might only makes sense in the Orion theme
                    if not (
                        any(t.value == style.weight for t in TextWeights)
                        or (1 <= int(style.weight) <= 1000)
                    ):
                        raise ValueError(
                            "'weight' param must be 'normal', 'bold' or integer number in range [1, 1000]"
                        )
                    self.weight = style.weight

                if style.size is not None and any(t.value == style.size for t in TextSizes):
                    self.size = style.size

                if style.color is not None:
                    self.color = style.color

        @property
        def align(self):
            return self.attributes.get("align")

        @align.setter
        def align(self, value: str):
            self.attributes["align"] = value

        @property
        def width(self):
            return self.attributes.get("width")

        @width.setter
        def width(self, value: str):
            self.attributes["width"] = value

        @property
        def height(self):
            return self.attributes.get("height")

        @height.setter
        def height(self, value: str):
            self.attributes["height"] = value

        @property
        def weight(self):
            return self.attributes.get("weight")

        @weight.setter
        def weight(self, value):
            self.attributes["weight"] = value

        @property
        def size(self):
            return self.attributes.get("size")

        @size.setter
        def size(self, value: str):
            self.attributes["size"] = value

        @property
        def color(self):
            return self.attributes.get("color")

        @color.setter
        def color(self, value: str):
            self.attributes["color"] = value

    class ColumnValue(StylableNode, ABC):
        def __init__(
            self,
            name,
            value,
            style: "MgrListData.Style" = None,
            attributes: dict = None,
            form: MgrForm = None,
        ):
            MgrListData.StylableNode.__init__(self, style=style, attributes=attributes)

            self.form = form
            self.name = name
            self.value = value

        @classmethod
        def from_element(cls, column_value_element: Element, form: MgrForm = None):
            return cls(column_value_element.tag, column_value_element.text, form=form)

        @abstractmethod
        def to_xml(self):
            column_value_element = Element(self.name)
            column_value_element.text = self.value
            return column_value_element

        @property
        def name(self):
            return self._name

        @name.setter
        def name(self, value):
            self._name = value

        @property
        def value(self):
            return self._value

        @value.setter
        def value(self, value):
            self._value = value

    class PriceValue(ColumnValue):
        class PriceTuple(NamedTuple):
            cost: Union[Decimal, float, int, str]
            currency: str

        def __init__(
            self,
            name,
            cost,
            currency,
            style: "MgrListData.Style" = None,
            attributes: dict = None,
            form: MgrForm = None,
        ):
            value = self.__class__.PriceTuple(cost, currency)
            super().__init__(name, value, style=style, attributes=attributes, form=form)

        @classmethod
        def from_element(cls, column_value_element: Element, form: MgrForm = None):
            column_name = column_value_element.tag
            price_element: Element = column_value_element.find("price")
            cost, currency = None, None
            for element in list(price_element):
                if element.tag == "cost":
                    cost = element.text
                elif element.tag == "currency":
                    currency = element.text
            return cls(column_name, cost, currency, form=form, attributes=price_element.attrib)

        def to_xml(self):
            attributes = {**self.attributes}
            column_value_element = Element(self.name, attrib=attributes)
            price_element = ET.SubElement(column_value_element, "price")
            ET.SubElement(price_element, "cost").text = str(self.value.cost)
            ET.SubElement(price_element, "currency").text = self.value.currency
            return column_value_element

    class Column(StylableNode, ABC):
        _type: ColumnTypes = None

        def __init__(
            self,
            name,
            style: "MgrListData.Style" = None,
            attributes: dict = None,
            form: MgrForm = None,
        ) -> None:
            MgrListData.StylableNode.__init__(self, style=style, attributes=attributes)

            self.form = form
            self.name = name
            # if align is not None and any(t.value == align for t in ColumnAlignTypes):
            #     self.align = align

            # dimension_pattern = r'^\d+px|\d+\%$'
            # if width is not None:
            #     if not re.match(dimension_pattern, width):
            #         raise ValueError("'width' param must be integer number with units, e.g. 10px, 50%")
            #     self.width = width

            # if height is not None and re.match(dimension_pattern, height):
            #     if not re.match(dimension_pattern, height):
            #         raise ValueError("'height' param must be integer number with units, e.g. 10px, 50%")
            #     self.height = height

            # if weight is not None:
            #     if not (any(t.value == weight for t in TextWeights) or (1 <= int(weight) <= 1000)):
            #         raise ValueError("'weight' param must be 'normal', 'bold' or integer number in range [1, 1000]")
            #     self.weight = int(weight)

            # if size is not None and any(t.value == size for t in TextSizes):
            #     self.size = size

            # if color is not None:
            #     self.color = color

            self.column_type = self.__class__._type.value

        @classmethod
        def from_element(cls, column_element: Element, form: MgrForm = None):
            name = column_element.get("name")
            return cls(name, form=form, attributes=column_element.attrib)

        @abstractmethod
        def get_value_from_element(column_value_element: Element) -> "MgrListData.ColumnValue":
            return MgrListData.ColumnValue.from_element(column_value_element)

        @property
        def name(self):
            return self.attributes.get("name")

        @name.setter
        def name(self, value: str):
            self.attributes["name"] = value

        @property
        def column_type(self):
            return self.attributes.get("type")

        @column_type.setter
        def column_type(self, value: str):
            self.attributes["type"] = value

        def to_xml(self):
            attributes = {**self.attributes}
            return Element("col", attrib=attributes)

    class DataColumn(Column):
        _type: ColumnTypes = ColumnTypes.DATA

        def get_value_from_element(column_value_element) -> str:
            return super().get_value_from_element(column_value_element).value

    class MessageColumn(Column):
        _type: ColumnTypes = ColumnTypes.MESSAGE

        def get_value_from_element(column_value_element) -> str:
            return super().get_value_from_element(column_value_element).value

    class ImageColumn(Column):
        _type: ColumnTypes = ColumnTypes.IMAGE

        def get_value_from_element(column_value_element) -> str:
            return super().get_value_from_element(column_value_element).value

    class PriceColumn(Column):
        _type: ColumnTypes = ColumnTypes.PRICE

        def get_value_from_element(column_value_element) -> "MgrListData.PriceValue":
            return MgrListData.PriceValue.from_element(column_value_element)

    class ButtonColumn(Column):
        _type: ColumnTypes = ColumnTypes.BUTTON

    class ControlColumn(Column):
        _type: ColumnTypes = ColumnTypes.CONTROL

    def __init__(
        self, name, form: MgrForm = None, columns: dict = None, attributes: dict = None
    ) -> None:
        super().__init__(name, form, attributes)
        self.columns = {}
        if columns:
            self.columns = columns

    @classmethod
    def create_column_from_element(cls, column_element: Element, form: MgrForm = None) -> Column:
        column_type = column_element.get("type")
        column_type = ColumnTypes(column_type)
        column = None
        if column_type is ColumnTypes.DATA:
            column = cls.DataColumn.from_element(column_element, form=form)
        elif column_type is ColumnTypes.MESSAGE:
            column = cls.MessageColumn.from_element(column_element, form=form)
        elif column_type is ColumnTypes.IMAGE:
            column = cls.ImageColumn.from_element(column_element, form=form)
        elif column_type is ColumnTypes.PRICE:
            column = cls.PriceColumn.from_element(column_element, form=form)
        elif column_type is ColumnTypes.BUTTON:
            column = cls.ButtonColumn.from_element(column_element, form=form)
        elif column_type is ColumnTypes.CONTROL:
            column = cls.ControlColumn.from_element(column_element, form=form)
        else:
            raise ValueError(f"Unknown column type '{column_type}'")

        return column

    def add_column(self, column: Column) -> Column:
        if column.name in self.columns:
            raise ValueError(f"Column with name '{column.name}' already exists")

        self.columns[column.name] = column
        return column

    def get_column(self, name: str) -> Column:
        return self.columns.get(name)

    def to_xml(self) -> Element:
        attributes = {**self.attributes}
        list_element = Element("list", attrib=attributes)
        for name, column in self.columns.items():
            # column_element = Element("col", attrib={"name": name, **column})
            list_element.append(column.to_xml())

        return list_element

    @classmethod
    def from_element(cls, field_element: Element, form: MgrForm = None) -> "MgrListData":
        list_name = field_element.get("name")
        columns = {}
        column_elements = list(field_element)
        for column_element in column_elements:
            # column_attributes = {**column_element.attrib}
            # column_name = column_attributes.pop("name")
            # columns[column_name] = column_attributes
            column = cls.create_column_from_element(column_element, form=form)
            columns[column.name] = column

        instance = cls(list_name, form=form, columns=columns, attributes=field_element.attrib)
        return instance
