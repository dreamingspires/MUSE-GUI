from typing import Dict
import PySimpleGUI as sg
from PySimpleGUI.PySimpleGUI import Element
from enum import Enum

from pydantic import BaseModel
from muse_gui.data_defs.abstract import Data


class CommodityType(str, Enum):
    energy = 'energy'
    environmental = 'environmental'


class Commodity(BaseModel):
    commodity: str
    commodity_type: CommodityType
    commodity_name: str
    c_emission_factor_co2: float
    heat_rate: float
    unit: str


class CommodityView(Data):
    model: Commodity

    def item(self) -> Dict[str, Element]:
        return {
            'commodity': sg.Input(self.model.commodity),
            'commodity_type': sg.DropDown([
                x.name for x in CommodityType
            ], default_value=self.model.commodity_type.name)
        }

    @classmethod
    def heading(cls) -> Dict[str, Element]:
        return {
            k: sg.Text(k.replace('_', '').title()) for k in [
                'commodity',
                'commodity_type',
            ]
        }
