from enum import Enum
from typing import List

from pydantic import BaseModel

from .abstract import Data


class CommodityType(str, Enum):
    energy = "Energy"
    environmental = "Environmental"


class CommodityPrice(BaseModel):
    region_name: str
    time: int
    value: float


class Commodity(Data):
    commodity: str
    commodity_type: CommodityType
    commodity_name: str
    c_emission_factor_co2: float
    heat_rate: float
    unit: str
    commodity_prices: List[CommodityPrice]
    price_unit: str
