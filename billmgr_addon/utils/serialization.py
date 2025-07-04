# -*- coding: utf-8 -*-

import json
from datetime import date, datetime, time
from decimal import Decimal
from typing import Any


def jsonify(o):
    return json.dumps(o, cls=CustomJSONEncoder)


class CustomJSONEncoder(json.JSONEncoder):
    def default(self, obj: Any) -> Any:
        if isinstance(obj, Decimal):
            return float(obj)
        elif isinstance(obj, (datetime, date, time)):
            return obj.isoformat()
        elif hasattr(obj, "__dict__"):
            return obj.__dict__
        return super().default(obj)
