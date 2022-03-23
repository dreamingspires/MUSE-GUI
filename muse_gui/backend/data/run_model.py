from typing import Any, Dict, List, Optional, Union

from pydantic import PositiveInt
from pydantic.class_validators import validator

from pydantic import BaseModel, validator, PositiveInt
from typing import List, Optional
from enum import Enum

from pydantic import BaseModel

class BaseSettings(BaseModel):
    class Config:
        use_enum_values = True

class MethodOptions(str, Enum):
    linear = 'linear'
    exponential = 'exponential'

class InterpolationMode(str, Enum):
    linear = 'linear'
    nearest = 'nearest'
    zero = 'zero'
    slinear = 'slinear'
    quadratic = 'quadratic'
    cubic = 'cubic'
    off = 'off'
    false = 'false'
    active = 'active'


class EquilibriumVariable(str, Enum):
    demand = 'demand'
    prices = 'prices'



class Sink(str, Enum):
    csv = 'csv'
    netcfd = 'netcfd'
    excel = 'excel'
    aggregate = 'aggregate'


class Quantity(str, Enum):
    capacity = 'capacity'
    prices = 'prices'
    supply = 'supply'

class Output(BaseSettings):
    quantity: Union[Quantity,Dict[str,Any]] = Quantity.capacity
    sink: Sink = Sink.csv
    filename: Optional[str] = None
    overwrite: bool = True
    keep_columns: Optional[List[str]] = None
    index: Optional[bool] = None

    @validator('filename', pre=True, always=True)
    def validate_filename(cls, value, values):
        if value is None:
            return '{cwd}/{default_output_dir}/{Sector}/'+values.quantity+'/{year}'+values.sink
        else:
            return value

class CarbonMarket(BaseSettings):
    budget: List[str] = []
    method: str = 'fitting'  # the one present method so far
    commodities: Optional[List[str]] = None
    control_undershoot: bool = True
    control_overshoot: bool = True
    method_options: Optional[MethodOptions] = None

class RunModel(BaseSettings):
    regions: List[str]
    time_framework: List[int]
    interest_rate: Optional[float] = None
    interpolation_mode: InterpolationMode = InterpolationMode.linear
    @validator('interpolation_mode', pre=True)
    def validate_case_insensitive(cls,v):
        return v.lower()
    log_level: str = 'info'
    equilibrium_variable: EquilibriumVariable = EquilibriumVariable.demand
    maximum_iterations: PositiveInt = 3
    tolerance: float = 0.1
    tolerance_unmet_demand: float = -0.1
    excluded_commodities: List[str] = [
        'CO2f', 'CO2r', 'CO2c', 'CO2s', 'CH4', 'N2O', 'f-gases']
    plugins: Optional[List[str]] = None
    foresight: int = 0
    carbon_budget_control: Optional[CarbonMarket] = None
