# coding=utf-8
from datetime import datetime
from typing import Union

from ...abc import AbstractDataTransformer
from fluent_compiler.types import FluentDateType, FluentNone, fluent_date


class DateTimeTransformer(AbstractDataTransformer):
    def __new__(cls, date: datetime, **kwargs) -> Union[FluentDateType, FluentNone]:
        return fluent_date(date, **kwargs)
