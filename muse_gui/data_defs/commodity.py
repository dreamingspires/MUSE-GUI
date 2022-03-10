from typing import Dict
import PySimpleGUI as sg
from PySimpleGUI.PySimpleGUI import Element
from enum import Enum

from pydantic import BaseModel
from muse_gui.data_defs.abstract import Data


class CommodityType(str, Enum):
    energy = 'energy'
    environmental = 'environmental'


class Commodity(Data):
    commodity: str
    commodity_type: CommodityType
    commodity_name: str
    c_emission_factor_co2: float
    heat_rate: float
    unit: str
