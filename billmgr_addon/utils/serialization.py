# -*- coding: utf-8 -*-

import json
from decimal import Decimal
from datetime import datetime, date, time
from typing import Any


class CustomJSONEncoder(json.JSONEncoder):
    """
    Кастомный JSON энкодер для BILLmanager объектов
    
    Поддерживает сериализацию:
    - Decimal в float
    - datetime, date, time в ISO строки
    - Другие специальные типы
    """
    
    def default(self, obj: Any) -> Any:
        """
        Кастомная сериализация объектов
        
        Args:
            obj: Объект для сериализации
            
        Returns:
            Any: Сериализованное представление
        """
        if isinstance(obj, Decimal):
            return float(obj)
        elif isinstance(obj, (datetime, date, time)):
            return obj.isoformat()
        elif hasattr(obj, '__dict__'):
            return obj.__dict__
        return super().default(obj) 