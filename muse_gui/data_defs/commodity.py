from typing import Dict, List
import PySimpleGUI as sg
from PySimpleGUI.PySimpleGUI import Element
from enum import Enum

from pydantic import BaseModel
from muse_gui.data_defs.abstract import Data


class CommodityType(str, Enum):
    energy = 'energy'
    environmental = 'environmental'


class CommodityPrice(BaseModel):
    region_name: str
    time: int
    value: float

class CommodityPrices(BaseModel):
    unit: str
    prices: List[CommodityPrice]

class Commodity(Data):
    commodity: str
    commodity_type: CommodityType
    commodity_name: str
    c_emission_factor_co2: float
    heat_rate: float
    unit: str
    commodity_prices: CommodityPrices
