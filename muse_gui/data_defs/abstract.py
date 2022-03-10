from typing import Dict
from pydantic import BaseModel
from PySimpleGUI.PySimpleGUI import Element


class Data(BaseModel):
    def item(self) -> Dict[str, Element]:
        raise NotImplementedError

    @classmethod
    def heading(cls) -> Dict[str, Element]:
        raise NotImplementedError



def construct_data_to_dropdown(enum: Type[Enum]) -> Callable[[str], DropDown]:
    def data_to_dropdown(data: str) -> DropDown:
        return sg.DropDown([
            x.name for x in enum
        ], default_value=data)
    return data_to_dropdown


class BaseDataView:
    __attrs__: Dict[str, Callable[[str], Element]]
    pass

def attrs_to_dataview(attrs: Dict[str, Callable[[str], Element]]) -> Type[BaseDataView]:
    class DataView(BaseDataView):
        def __init__(self, data: Commodity) -> None:
            for k, v in attrs.items():
                setattr(self, k, v(getattr(data, k)))
            self.__attrs___ = attrs
        def __iter__(self) -> Iterable[Element]:
            pass
        def __getitem__(self, item: str) -> Element:
            pass
    return DataView

class DataViewGenerator:
    def __init__(self, **attrs: Callable[[str], Element]):
        self.attrs = attrs
        self.data_view = attrs_to_dataview(attrs)
    def __call__(self, data: Commodity) -> DataView:
        return self.data_view(data)


def input_func(data:str) -> Input:
    return sg.Input(data,expand_x = True, size=(10,10))