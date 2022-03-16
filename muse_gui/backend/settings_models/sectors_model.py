from pydantic import BaseModel, validator
from typing import Any, Dict, List, Optional, Union, Literal
from enum import Enum

class Investment_production(str, Enum):
    share = 'share'
    match = 'match'


class Demand_share(str, Enum):
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


class Output(BaseModel):
    quantity: Union[Quantity,Dict[str,Any]] = 'capacity'
    sink: Sink = Sink.csv
    filename: str = None
    overwrite: bool = False
    keep_columns: Optional[List[str]] = None
    index: Optional[bool] = False

    @validator('filename', pre=True, always=True)
    def validate_filename(cls, value, values):
        if value is None:
            return '{cwd}/{default_output_dir}/{Sector}/'+values.quantity+'/{year}'+values.sink
        else:
            return value

class Subsector(BaseModel):
    agents: str = None
    constraints: List[str] = None
    demand_share: str = None
    existing_capacity: str = None
    forecast: int = None
    lpsolver: str = None

class Net(str, Enum):
    net = 'new_to_retro'

class Interactions(BaseModel):
    interaction: Interaction = 'default'
    net: Net = 'new_to_retro'

class StandardSector(BaseModel):
    type: Literal['default'] = "default"
    priority: int = 100
    check_standard_prio = validator(
        'priority', pre=True, allow_reuse=True)(validate_priority)
    interpolation: Optional[str] = None
    investment_production: Investment_production = Investment_production.share
    # not really defined so I can't create enum type
    dispatch_production: Optional[str] = None
    demand_share: Demand_share = Demand_share.new_and_retro
    interactions:List[Interactions] = None 
    timeslices: Dict[str, Any] = None
    outputs: Optional[List[Output]] = None
    # should be path to csv file
    technodata: str = None
    timeslice_levels: List[str] = ["month", "day", "hour"]
    # should be path to csv file
    commodities_in: str = None
    commodities_out: str = None
    existing_capacity: str = None
    agents: str = None
    subsectors:Dict[str,Subsector] = None        




class StandardSectorExample(BaseModel):
    commodities_in: str = None
    commodities_out: str = None
    dispatch_production: Investment_production = 'share'
    interactions:List[Interactions] = None 
    outputs: List[Output]
    priority: int = 100
    check_standard_example_prio = validator(
        'priority', pre=True, allow_reuse=True)(validate_priority)          
    subsectors:Dict[str,Subsector] = None        
    technodata: str = None
    type: Literal['default'] = "default"


class PresetSector(BaseModel):
    type: Literal['presets'] = 'presets'
    priority: int = 100
    check_preset_prio = validator(
        'priority', pre=True, allow_reuse=True)(validate_priority)
    timeslices_levels: List[str] = ["month", "day", "hour"]
    consumption_path: str = None
    supply_path: str = None
    prices_path: str = None
    demand_path: str = None
    macrodrivers_path: str = None
    regression_path: str = None
    timeslice_shares_path: Optional[str] = None
    filters: Optional[Dict[str, Any]]


class LegacySector(BaseModel):
    type: Literal['legacy'] = 'legacy'
    priority: int = 100
    check_legacy_prio = validator(
        'priority', pre=True, allow_reuse=True)(validate_priority)
    agregation_level: str = None
    excess: int = 0
    timeslices_path: str = None
    userdata_path: str = None
    technodata_path: str = None
    output_path: str = None
