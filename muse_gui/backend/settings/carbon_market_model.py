from pydantic import BaseModel, validator, PositiveInt
from typing import List, Optional
from enum import Enum
from .base import BaseSettings

class MethodOptions(str, Enum):
    linear = 'linear'
    exponential = 'exponential'


class CarbonMarket(BaseSettings):
    budget: List[str] = []
    method: str = 'fitting'  # the one present method so far
    commodities: Optional[List[str]] = None
    control_undershoot: bool = True
    control_overshoot: bool = True
    method_options: Optional[MethodOptions] = None