from pydantic import BaseModel, validator, PositiveInt
from typing import List, Optional
from enum import Enum
from sectors_model import Output

class Interpolation_mode(str, Enum):
    linear = 'linear'
    nearest = 'nearest'
    zero = 'zero'
    slinear = 'slinear'
    quadratic = 'quadratic'
    cubic = 'cubic'
    off = 'off'
    false = 'false'
    active = 'Active'


class Equilibirum_variable(str, Enum):
    demand = 'demand'
    prices = 'prices'

class MainSettings(BaseModel):
    time_framework: List[int] = None
    regions: List[str] = None
    interest_rate: float = None
    interpolation_mode: Interpolation_mode = Interpolation_mode.linear
    log_level: str = 'info'
    outputs: List[Output] = None
    equilibirum_variable: Equilibirum_variable = Equilibirum_variable.demand
    maximum_iterations: PositiveInt = 3
    tolerance: float = 0.1
    tolerance_unmet_demand: float = -0.1
    excluded_commodities: List[str] = [
        'CO2f', 'CO2r', 'CO2c', 'CO2s', 'CH4', 'N2O', 'f-gases']
    plugins: List[str] = None
    foresight: int = 0