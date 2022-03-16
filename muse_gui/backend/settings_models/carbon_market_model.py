from pydantic import BaseModel, validator, PositiveInt
from typing import List, Optional
from enum import Enum

class Method_options(str, Enum):
    linear = 'linear'
    exponential = 'exponential'


class CarbonMarket(BaseModel):
    budget: List[str] = []
    method: str = 'fitting'  # the one present method so far
    commodities: List[str] = None
    control_undershoot: bool = True
    control_overshoot: bool = True
    method_options: Method_options = None