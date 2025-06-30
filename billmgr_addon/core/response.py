 # -*- coding: utf-8 -*-

import xml.etree.ElementTree as ET
from flask import Response
import logging


class MgrResponse:
    """
    Базовый класс для ответов MGR запросов
    
    Все ответы BILLmanager должны быть в формате XML.
    """
    
    def __init__(self, xml_data=None):
        self.xml_data = xml_data or "<doc></doc>"

    def to_response(self) -> Response:
        """Преобразование в Flask Response"""
        return Response(
            self.xml_data,
            mimetype='application/xml',
            headers={'Content-Type': 'application/xml; charset=utf-8'}
        )

    def __str__(self):
        return self.xml_data


class MgrErrorResponse(MgrResponse):
    """Ответ с ошибкой"""
    
    def __init__(self, error_message="Unknown error", error_code=None):
        # Создание XML с ошибкой
        root = ET.Element("doc")
        error_elem = ET.SubElement(root, "error")
        
        if error_code:
            error_elem.set("code", str(error_code))
        
        error_elem.text = str(error_message)
        
        xml_data = ET.tostring(root, encoding='unicode')
        super().__init__(xml_data)
        
        logging.error(f"MGR Error Response: {error_message}")


class MgrUnknownErrorResponse(MgrErrorResponse):
    """Ответ с неизвестной ошибкой"""
    
    def __init__(self):
        super().__init__("Internal server error", "UNKNOWN_ERROR")


class MgrSuccessResponse(MgrResponse):
    """Ответ об успешном выполнении"""
    
    def __init__(self, message="Success"):
        root = ET.Element("doc")
        ok_elem = ET.SubElement(root, "ok")
        ok_elem.text = str(message)
        
        xml_data = ET.tostring(root, encoding='unicode')
        super().__init__(xml_data)


class MgrOkResponse(MgrResponse):
    """Простой OK ответ для processing modules"""
    
    def __init__(self, message=""):
        root = ET.Element("doc")
        if message:
            root.text = str(message)
        
        xml_data = ET.tostring(root, encoding='unicode')
        super().__init__(xml_data)


# Вспомогательный класс для файлов
class DownloadFileData:
    """Данные для скачивания файлов"""
    
    def __init__(self, content=b"", filename="file.txt", content_type="text/plain"):
        self.content = content
        self.filename = filename
        self.content_type = content_type


__all__ = [
    'MgrResponse',
    'MgrErrorResponse', 
    'MgrUnknownErrorResponse',
    'MgrSuccessResponse',
    'MgrOkResponse',
    'DownloadFileData'
]