import PySimpleGUI as sg

from typing import Type, Callable
from enum import Enum
from .data_view_generator import DataViewGenerator
from muse_gui.data_defs.commodity import Commodity, CommodityType

def construct_data_to_dropdown(enum: Type[Enum]) -> Callable[[str], sg.DropDown]:
    def data_to_dropdown(data: str) -> sg.DropDown:
        return sg.DropDown([
            x.name for x in enum
        ], default_value=data, expand_x = True,  size=(10,10))
    return data_to_dropdown

def data_to_input(data:str) -> sg.Input:
    return sg.Input(data,expand_x = True, size=(10,10))

CommodityView = DataViewGenerator[Commodity](
    Commodity, 
    commodity = data_to_input, 
    commodity_type = construct_data_to_dropdown(CommodityType)
)

"""
sg.Text(k.replace('_', '').title(), expand_x = True) for k in [
                'commodity',
                'commodity_type',
            ]
"""