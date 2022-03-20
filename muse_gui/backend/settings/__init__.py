from pydantic import BaseModel, Field, validator
from typing import Annotated, Any, Dict, List, Optional, Union

from muse_gui.backend.resources.datastore.exceptions import LevelNameMismatch

from .base import BaseSettings
from .carbon_market_model import CarbonMarket
from .global_input_files_model import GlobalInputFiles
from .sectors_model import PresetSector, LegacySector, StandardSector, Output
from pydantic import BaseModel, PositiveInt
from typing import List, Optional
from enum import Enum
from muse_gui.backend.utils import unpack_timeslice
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
    sectors: Dict[str, Annotated[Union[StandardSector, PresetSector, LegacySector], Field(discriminator='type')]]
    interest_rate: Optional[float] = None
    interpolation_mode: Interpolation_mode = Interpolation_mode.linear
    @validator('interpolation_mode', pre=True)
    def validate_case_insensitive(cls,v):
        return v.lower()
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

    timeslices: Dict[str, Any]
    @validator('timeslices')
    def validate_timeslice(cls, v):
        time_slice_info = unpack_timeslice(v)
        time_slice_names = list(time_slice_info.timeslices.keys())
        break_down_names = [i.split('.') for i in time_slice_names]
        for break_down_name in break_down_names:
            if len(break_down_name) != len(time_slice_info.level_names):
                raise LevelNameMismatch(time_slice_info.level_names, break_down_name)
        return v


