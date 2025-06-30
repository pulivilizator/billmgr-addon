# coding=utf-8
from datetime import datetime
from typing import Union

from fluent_compiler.types import fluent_date, FluentDateType, FluentNone

from app.fluentbillmgr.src.abc import AbstractDataTransformer


class DateTimeTransformer(AbstractDataTransformer):
    def __new__(
            cls,
            date: datetime,
            **kwargs
    ) -> Union[FluentDateType, FluentNone]:
        return fluent_date(
            date,
            **kwargs
        )
