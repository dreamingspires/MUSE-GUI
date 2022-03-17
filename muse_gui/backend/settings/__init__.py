from pydantic import BaseModel, Field
from typing import Annotated, Any, Dict, List, Optional, Union

from .base import BaseSettings
from .carbon_market_model import CarbonMarket
from .global_input_files_model import GlobalInputFiles
from .sectors_model import PresetSector, LegacySector, StandardSector, Output
from pydantic import BaseModel, PositiveInt
from typing import List, Optional
from enum import Enum

class Interpolation_mode(str, Enum):
    linear = 'linear'
    nearest = 'nearest'
    zero = 'zero'
    slinear = 'slinear'
    quadratic = 'quadratic'
    cubic = 'cubic'
    off = 'off'
    false = 'false'
    active = 'active'


class Equilibirum_variable(str, Enum):
    demand = 'demand'
    prices = 'prices'



class SettingsModel(BaseSettings):
    global_input_files: GlobalInputFiles
    time_framework: List[int]
    regions: List[str]
    interest_rate: Optional[float] = None
    interpolation_mode: Interpolation_mode = Interpolation_mode.linear
    log_level: str = 'info'
    outputs: Optional[List[Output]] = None
    equilibirum_variable: Equilibirum_variable = Equilibirum_variable.demand
    maximum_iterations: PositiveInt = 3
    tolerance: float = 0.1
    tolerance_unmet_demand: float = -0.1
    excluded_commodities: List[str] = [
        'CO2f', 'CO2r', 'CO2c', 'CO2s', 'CH4', 'N2O', 'f-gases']
    plugins: Optional[List[str]] = None
    foresight: int = 0
    carbon_budget_control: Optional[CarbonMarket] = None
    sectors: Optional[Dict[str, Annotated[Union[StandardSector, PresetSector, LegacySector], Field(discriminator='type')]]] = None
    timeslices: Dict[str, Any]
