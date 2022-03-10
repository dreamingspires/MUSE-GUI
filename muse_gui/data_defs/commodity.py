from typing import Dict
import PySimpleGUI as sg
from PySimpleGUI.PySimpleGUI import Element
from enum import Enum
from muse_gui.data_defs.abstract import Data


class CommodityType(Enum):
    energy = 'energy'
    environmental='environmental'

class Commodity(Data):
    commodity: str
    commodity_type: CommodityType
    commodity_name: str
    c_emission_factor_co2: float
    heat_rate: float
    unit: str

    def item(self) -> Dict[str,Element]:
        return {
            'commodity': sg.Input(self.commodity,expand_x = True, size=(10,10)),
            'commodity_type': sg.Input(str(self.commodity_type),expand_x = True,  size=(10,10))
        }
    
    @classmethod
    def heading(cls) -> Dict[str, Element]:
        return {
            'commodity': sg.Text('Commodity',expand_x = True),
            'commodity_type': sg.Text('CommodityType',expand_x = True),
        }
