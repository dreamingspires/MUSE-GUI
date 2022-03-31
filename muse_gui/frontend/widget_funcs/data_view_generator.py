from typing import Callable, Dict, Generic, Iterator, Type, TypeVar

import PySimpleGUI as sg
from PySimpleGUI.PySimpleGUI import Element

from muse_gui.backend.data.abstract import Data

DataType = TypeVar("DataType", bound=Data)


class BaseDataView(Generic[DataType]):
    __attrs__: Dict[str, Callable[[str], Element]]

    def __init__(self, data: DataType) -> None:
        raise NotImplementedError

    def __iter__(self) -> Iterator[Element]:
        raise NotImplementedError

    def __getitem__(self, item: str) -> Element:
        raise NotImplementedError


def attrs_to_dataview(
    attrs: Dict[str, Callable[[str], Element]], data_type: Type[Data]
) -> Type[BaseDataView]:
    class DataView(BaseDataView, Iterator[Element], Generic[DataType]):
        def __init__(self, data: Data) -> None:
            for k, v in attrs.items():
                setattr(self, k, v(getattr(data, k)))
            self.__attrs___ = attrs

        def __iter__(self) -> Iterator[Element]:
            self._iterator = iter([getattr(self, i) for i in self.__attrs___.keys()])
            return self

        def __next__(self):
            return next(self._iterator)

    return DataView[data_type]


class DataViewGenerator(Generic[DataType]):
    def __init__(self, data_type: Type[Data], **attrs: Callable[[str], Element]):
        self.attrs = attrs
        self.data_view = attrs_to_dataview(attrs, data_type)
        self.data_type = data_type

    def __call__(self, data: Data) -> BaseDataView[DataType]:
        return self.data_view(data)
