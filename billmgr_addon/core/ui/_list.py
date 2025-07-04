# -*- coding: utf-8 -*-

import xml.etree.ElementTree as ET
from typing import List, Union
from xml.etree.ElementTree import Element

from . import MgrUI


class MgrList(MgrUI):
    def _init_ui_objects(self):
        self.key_field = self.messages_element.get("key")
        self.name_field = self.messages_element.get("keyname", self.key_field)

        toolbar_element = self.metadata_element.find("toolbar")
        self.toolbar: MgrToolbar = MgrToolbar.from_element(toolbar_element, mgr_list=self)

        self.columns = {}
        columns_data_element = self.metadata_element.find("coldata")
        if columns_data_element:
            for column_element in list(columns_data_element):
                name = column_element.get("name")
                self.columns[name] = MgrColumn.from_element(column_element, mgr_list=self)

    def _init_data(self):
        # self.params = {}
        self.data_rows = []

        self.parent_id = self._get_root_child_element_text("plid")
        self.parent_name = self._get_root_child_element_text("plname")
        self.total_count = self._get_root_child_element_text("p_elems")
        self.page_number = self._get_root_child_element_text("p_num")
        self.on_page_count = self._get_root_child_element_text("p_cnt")
        self.sort_field = self._get_root_child_element_text("p_sort")
        self.sort_order = self._get_root_child_element_text("p_order")

        self.page_names = []
        page_name_elements = self.root.findall("page")
        for page_name_element in page_name_elements:
            self.page_names = page_name_element.text

        row_elements = self.root.findall("elem")
        for row_element in row_elements:
            data_row = {}
            for value_element in list(row_element):
                # TODO - use MgrColumn to parse value?
                data_row[value_element.tag] = value_element.text

            self.data_rows.append(data_row)

    # TODO - pagination.
    # 5 pages by 1000 rows max? Or use panel pagination settings?
    # generate page names from first and last row on page?
    # def set_pagination(self, rows, page_name_key:str='id'):
    # pass

    @classmethod
    def _remap_dict(cls, keys_map, source_dict):
        return {keys_map[k]: source_dict.get(k, None) for k in keys_map}

    def set_data_rows(
        self,
        rows: list,
        parent_list_id=None,
        column_names: Union[dict, list, None] = None,
        formatters: dict = None,
    ):
        self.data_rows = []
        new_rows = []
        # for row in rows:
        #     pass

        if isinstance(column_names, list):
            for row in rows:
                if isinstance(row, list):
                    new_rows.append(dict(zip(column_names, row)))
                else:
                    raise TypeError("Can not name columns. Data row has to be list")
        elif isinstance(column_names, dict):
            for row in rows:
                if isinstance(row, dict):
                    new_rows.append(MgrList._remap_dict(column_names, row))
                else:
                    raise TypeError("Can not name columns. Data row has to be dict")
        else:
            for row in rows:
                if isinstance(row, dict):
                    new_rows.append(row)
                else:
                    raise TypeError("Unknown type of data row. It has to be dict")

        self.data_rows = new_rows
        # TODO - formatting
        # for row in rows:
        #     elem_element = ET.SubElement(self.root, 'elem')
        #     for name, value in row.items():
        #         cell_value = value
        #         if formatters is not None:
        #             formatter = formatters.get(name)
        #             if formatter is not None:
        #                 cell_value = formatter(value)

        #         cell_element = ET.SubElement(elem_element, name)
        #         if cell_value is not None:
        #             cell_element.text = str(cell_value)

        # ET.SubElement(self.root, 'p_elems').text = str(len(rows))
        # if parent_list_id is not None:
        #     ET.SubElement(self.root, 'plid').text = str(parent_list_id)

    def patch_xml(self):
        self.metadata_element.append(self.toolbar.to_xml())
        columns_data_element = ET.SubElement(self.metadata_element, "coldata")
        for name, column in self.columns.items():
            columns_data_element.append(column.to_xml())

        for name, message in self.messages.items():
            ET.SubElement(self.messages_element, "msg", attrib={"name": name}).text = str(message)

        for row in self.data_rows:
            row_element = Element("elem")
            for name, value in row.items():
                ET.SubElement(row_element, name).text = str(value)

            self.root.append(row_element)

        if self.parent_id is not None:
            ET.SubElement(self.root, "plid").text = str(self.parent_id)

        if self.parent_name is not None:
            ET.SubElement(self.root, "plname").text = str(self.parent_name)

        if self.total_count is not None:
            ET.SubElement(self.root, "p_elems").text = str(self.total_count)

        if self.page_number is not None:
            ET.SubElement(self.root, "p_num").text = str(self.page_number)

        if self.on_page_count is not None:
            ET.SubElement(self.root, "p_cnt").text = str(self.on_page_count)

        for page_name in self.page_names:
            ET.SubElement(self.root, "page").text = str(page_name)

        if self.sort_field is not None:
            ET.SubElement(self.root, "p_sort").text = str(self.sort_field)

        if self.sort_order is not None:
            ET.SubElement(self.root, "p_order").text = str(self.sort_order)

        # form_element = ET.SubElement(self.metadata_element, 'form', attrib={
        #     'title': self.title_tag,
        #     'nosubmit': 'no' if self.has_submit_button else 'yes',
        #     'nocancel': 'no' if self.has_cancel_button else 'yes',
        #     'noback': 'no' if self.has_back_button else 'yes',
        # })
        # for name, page in self.pages.items():
        #     if name is None:
        #         for form_group_element in list(page.to_xml()):
        #             form_element.append(form_group_element)
        #     else:
        #         form_element.append(page.to_xml())

        # for name, message in self.messages.items():
        #     ET.SubElement(self.messages_element, 'msg', attrib={'name': name}).text = message

        # for name, value in self.field_data.items():
        #     ET.SubElement(self.root, name).text = value

        # for key, options in self.field_options.items():
        #     list_element = ET.SubElement(self.root, 'slist')
        #     for option in options:
        #         option_element = Element('val', attrib={'key': option['key']})
        #         option_element.text = option['label']
        #         list_element.append(option_element)

    # @property
    # def title_tag(self):
    #     return self.form_element.get('title', 'elid')

    # @title_tag.setter
    # def title_tag(self, value):
    #     self.form_element.set('title', value)

    # @property
    # def parent_id(self):
    #     return self.params.get('elid')

    # @parent_id.setter
    # def parent_id(self, value):
    #     # TODO - also change tag value?
    #     self.params['elid'] = value

    # @property
    # def parent_title(self):
    #     return self.params.get(self.title_tag)

    # @parent_title.setter
    # def parent_title(self, value):
    #     # TODO - also change tag value?
    #     self.params[self.title_tag] = value

    # @property
    # def values(self):
    #     pass

    # def set_values(self, values):
    #     pass


# <toolbar>
class MgrToolbar:
    def __init__(
        self, mgr_list: MgrList = None, groups: dict = None, attributes: dict = None
    ) -> None:
        self.list = mgr_list
        self.groups = groups
        self.attributes = {}
        if attributes:
            self.attributes = {**attributes}

    @classmethod
    def from_element(cls, toolbar_element: Element, mgr_list: MgrList = None):
        group_elements = list(toolbar_element)
        groups = {
            el.attrib["name"]: MgrToolGroup.from_element(el, mgr_list=mgr_list)
            for el in group_elements
        }
        instance = cls(mgr_list=mgr_list, groups=groups, attributes=toolbar_element.attrib)
        return instance

    def to_xml(self):
        attributes = {**self.attributes}
        toolbar_element = Element("toolbar", attrib=attributes)
        for name, group in self.groups.items():
            toolbar_element.append(group.to_xml())
        return toolbar_element


# <toolgrp>
class MgrToolGroup:
    def __init__(
        self,
        name,
        mgr_list: MgrList = None,
        buttons: dict = None,
        attributes: dict = None,
    ) -> None:
        self.name = name
        self.list = mgr_list
        self.buttons = buttons
        self.attributes = {}
        if attributes:
            self.attributes = {**attributes}

    @classmethod
    def from_element(cls, group_element: Element, mgr_list: MgrList = None):
        name = group_element.get("name")
        button_elements = list(group_element)

        buttons = {}
        for button_element in button_elements:
            button = MgrToolButton.from_element(button_element, mgr_list=mgr_list)
            # field = None
            # if field_element.tag == 'textdata':
            #     field = MgrTextData.from_element(field_element, form=form)
            # elif field_element.tag == 'textarea':
            #     continue
            # elif field_element.tag == 'select':
            #     continue
            # elif field_element.tag == 'slider':
            #     continue
            # elif field_element.tag == 'input':
            #     continue
            # else:
            #     continue

            buttons[button.name] = button

        instance = cls(name, mgr_list=mgr_list, buttons=buttons, attributes=group_element.attrib)
        return instance

    def to_xml(self):
        attributes = {**self.attributes}
        attributes["name"] = self.name
        group_element = Element("toolgrp", attrib=attributes)
        for name, button in self.buttons.items():
            group_element.append(button.to_xml())
        return group_element


# <toolbtn>
class MgrToolButton:
    class VisibilityCondition:
        def __init__(
            self, condition_type: str, column_name: str, value: str, mgr_list: MgrList = None
        ):
            """
            condition_type: (show, hide, remove) applied visibility status when condition is true
            column_name: column name to get values from
            value: condition is true when column in the row has this value
            """
            self.list = mgr_list
            self.condition_type = condition_type
            self.column_name = column_name
            self.value = value

        @classmethod
        def from_element(cls, field_element: Element, mgr_list: MgrList = None):
            condition_type = field_element.tag
            column_name = field_element.get("name")
            value = field_element.get("value")
            return cls(condition_type, column_name, value, mgr_list=mgr_list)

        def to_xml(self):
            attributes = {"name": self.column_name, "value": self.value}

            return Element(self.condition_type, attrib=attributes)

    def __init__(
        self,
        name,
        button_type,
        mgr_list: MgrList = None,
        attributes: dict = None,
        conditions: List[VisibilityCondition] = None,
    ) -> None:
        self.name = name
        self.type = button_type
        self.list = mgr_list
        self.attributes = {}
        if attributes:
            self.attributes = {**attributes}

        self.conditions = []
        if conditions is not None:
            self.conditions = conditions

    @classmethod
    def from_element(cls, button_element: Element, mgr_list: MgrList = None):
        name = button_element.get("name")
        button_type = button_element.get("type")

        conditions = []
        condition_elements = list(button_element)
        for condition_element in condition_elements:
            condition = cls.VisibilityCondition.from_element(condition_element, mgr_list=mgr_list)
            conditions.append(condition)

        instance = cls(
            name,
            button_type,
            mgr_list=mgr_list,
            attributes=button_element.attrib,
            conditions=conditions,
        )
        return instance

    def to_xml(self):
        attributes = {**self.attributes}
        attributes["name"] = self.name
        attributes["type"] = self.type
        button_element = Element("toolbtn", attrib=attributes)
        for condition in self.conditions:
            condition_element = condition.to_xml()
            button_element.append(condition_element)

        return button_element


# <col>
class MgrColumn:
    def __init__(
        self,
        name,
        column_type,
        mgr_list: MgrList = None,
        is_hidden=False,
        attributes: dict = None,
    ) -> None:
        self.name = name
        self.type = column_type
        self.list = mgr_list
        self.is_hidden = is_hidden
        self.attributes = {}
        if attributes:
            self.attributes = {**attributes}

    @classmethod
    def from_element(cls, column_element: Element, mgr_list: MgrList = None):
        name = column_element.get("name")
        column_type = column_element.get("type")
        is_hidden = column_element.get("hidden") == "yes"
        instance = cls(
            name,
            column_type,
            mgr_list=mgr_list,
            is_hidden=is_hidden,
            attributes=column_element.attrib,
        )
        return instance

    def to_xml(self):
        attributes = {**self.attributes}
        attributes["name"] = self.name
        attributes["type"] = self.type
        attributes["hidden"] = "yes" if self.is_hidden else "no"
        return Element("col", attrib=attributes)
