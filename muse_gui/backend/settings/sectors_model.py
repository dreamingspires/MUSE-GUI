from pydantic import BaseModel, validator
from typing import Any, Dict, List, Optional, Union, Literal
from enum import Enum
from .base import BaseSettings
class InvestmentProduction(str, Enum):
    share = 'share'
    match = 'match'


class DemandShare(str, Enum):
    new_and_retro = 'new_and_retro'


class Interaction(str, Enum):
    default = 'default'
    transfer = 'transfer'


class Quantity(str, Enum):
    capacity = 'capacity'
    prices = 'prices'
    supply = 'supply'


class Sink(str, Enum):
    csv = 'csv'
    netcfd = 'netcfd'
    excel = 'excel'
    aggregate = 'aggregate'





class Output(BaseSettings):
    quantity: Union[Quantity,Dict[str,Any]] = Quantity.capacity
    sink: Sink = Sink.csv
    filename: Optional[str] = None
    overwrite: bool = False
    keep_columns: Optional[List[str]] = None
    index: Optional[bool] = False

    @validator('filename', pre=True, always=True)
    def validate_filename(cls, value, values):
        if value is None:
            return '{cwd}/{default_output_dir}/{Sector}/'+values.quantity+'/{year}'+values.sink
        else:
            return value

class Subsector(BaseSettings):
    agents: str
    existing_capacity: str
    constraints: Optional[List[str]] = None
    demand_share: Optional[str] = None
    forecast: Optional[int] = None
    lpsolver: Optional[str] = None

class Net(str, Enum):
    new_to_retro = 'new_to_retro'

class Interactions(BaseSettings):
    interaction: Interaction = Interaction.default
    net: Net = Net.new_to_retro

class BaseSector(BaseSettings):
    priority: int = 100
    @validator('priority', pre=True, allow_reuse=True)
    def validate_priority(cls, value):
        if value == 'preset':
            return 0
        elif value == 'demand':
            return 10
        elif value == 'conversion':
            return 20
        elif value == 'supply':
            return 30
        elif value == 'last':
            return 100
        else:
            assert isinstance(value, int)
            return value

class InterpolationType(str, Enum):
    """
    See check_interpolation_mode in [toml.py](https://github.com/SGIModel/MUSE_ICL/blob/856bec4652c50e16413a353b98280024b2e9ddc4/src/muse/readers/toml.py#L688)
    """
    NEAREST = 'nearest'
    LINEAR = 'linear'
    CUBIC = 'cubic'

class StandardSector(BaseSector):
    type: Literal['default'] = "default"
    technodata: str
    commodities_in: str
    commodities_out: str
    subsectors: Dict[str,Subsector]
    interpolation: InterpolationType = InterpolationType.LINEAR
    investment_production: InvestmentProduction = InvestmentProduction.share
    # not really defined so I can't create enum type
    dispatch_production: Optional[str] = None
    demand_share: DemandShare = DemandShare.new_and_retro
    interactions: Optional[List[Interactions]] = None 
    timeslices: Optional[Dict[str, Any]] = None
    outputs: Optional[List[Output]] = None
    timeslice_levels: List[str] = ["month", "day", "hour"]
    existing_capacity: Optional[str] = None
    # should be path to csv file
    agents: Optional[str] = None



class PresetSector(BaseSector):
    type: Literal['presets'] = 'presets'
    timeslices_levels: List[str] = ["month", "day", "hour"]
    consumption_path: str
    supply_path: Optional[str] = None
    prices_path: Optional[str] = None
    demand_path: Optional[str] = None
    macrodrivers_path: Optional[str] = None
    regression_path: Optional[str] = None
    timeslice_shares_path: Optional[str] = None
    filters: Optional[Dict[str, Any]]


class LegacySector(BaseSector):
    type: Literal['legacy'] = 'legacy'
    agregation_level: Optional[str] = None
    excess: int = 0
    timeslices_path: Optional[str] = None
    userdata_path: Optional[str] = None
    technodata_path: Optional[str] = None
    output_path: Optional[str] = None
