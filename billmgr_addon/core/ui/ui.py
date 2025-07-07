# -*- coding: utf-8 -*-

import xml.etree.ElementTree as ET
from abc import ABC, abstractmethod
from xml.etree.ElementTree import Element

from billmgr_addon.utils.logging import LOGGER

from ..request_types import MgrRequest


class MgrError(Exception):
    def __init__(self, message):
        self.message = message


class MgrNode(ABC):
    # attributes = {}

    def __init__(self, name=None, level=8) -> None:
        self.name = name
        self.level = level
        self.xml_element: Element = None

    @property
    def level(self):
        return self._level

    @level.setter
    def level(self, value):
        # FIXME - check if 8 is the lowest possible level
        self._level = value

    @abstractmethod
    def to_xml_element(self) -> Element:
        raise NotImplementedError

    @classmethod
    @abstractmethod
    def from_xml_element(cls, xml_element: Element) -> "MgrNode":
        # for name, value in xml_element.attrib.items():
        raise NotImplementedError

    # def mgr_attribute(cls, name, attribute_type):
    #     attribute = cls.attributes.get(name)
    #     if attribute is None:
    #         cls.attributes[name] = attribute_type()


class MgrUnknownNode:
    def __init__(self, xml_string: str, name):
        self.name = name
        self.original_xml = xml_string

    @classmethod
    def from_element(cls, xml_element: Element):
        name = xml_element.get("name")
        xml_string = ET.tostring(xml_element, encoding="unicode", method="xml")
        return cls(xml_string, name)

    def to_xml(self):
        try:
            return ET.fromstring(self.original_xml)
        except ET.ParseError:
            LOGGER.error("Could not parse XML from XML input string.")
            raise


class MgrUI(ABC):
    def __init__(self, xml_input_string) -> None:
        self.original_xml = xml_input_string
        self.root = self._parse_xml(xml_input_string)

        self._init_metadata()
        self._init_messages()
        self._init_ui_objects()
        self._init_data()
        self._clear_doc()

    @classmethod
    def from_request(cls, mgr_request: MgrRequest) -> "MgrUI":
        return cls(mgr_request.xml_input)

    def _parse_xml(self, xml_input_string) -> Element:
        try:
            return ET.fromstring(xml_input_string)
        except ET.ParseError:
            LOGGER.error("Could not parse XML from XML input string.")
            raise

    def _init_metadata(self):
        metadata_element = self.root.find("./metadata")
        self.metadata_element = metadata_element
        self.action_name = metadata_element.get("name")
        self.ui_type = metadata_element.get("type")

    def _init_messages(self):
        messages_element = self.root.find("./messages")
        self.messages_element = messages_element
        self.messages = {}
        list()
        for message_element in list(messages_element):
            name = message_element.get("name")
            self.messages[name] = message_element.text

    @abstractmethod
    def _init_ui_objects(self):
        raise NotImplementedError

    @abstractmethod
    def _init_data(self):
        raise NotImplementedError

    def _clear_doc(self):
        new_root = Element(self.root.tag, attrib=self.root.attrib)
        new_metadata_element = ET.SubElement(
            new_root, "metadata", attrib=self.metadata_element.attrib
        )
        new_messages_element = ET.SubElement(
            new_root, "messages", attrib=self.messages_element.attrib
        )
        self.root = new_root
        self.metadata_element = new_metadata_element
        self.messages_element = new_messages_element

    def __str__(self) -> str:
        # self.patch_xml()
        return ET.tostring(self.root, encoding="unicode", method="xml")

    @abstractmethod
    def patch_xml(self):
        raise NotImplementedError

    def _get_root_child_element_text(self, tag):
        element = self.root.find(tag)
        if element:
            return element.text

        return None
