# coding=utf-8
from abc import ABC, abstractmethod
from typing import Any


class AbstractDataTransformer(ABC):
    @abstractmethod
    def __new__(cls, data: Any, **kwargs) -> Any:
        raise NotImplementedError
