from pydantic import BaseModel, validator
from typing import Any, Dict, Enum, List, Optional


class Type(str, Enum):
    default = 'default'
    presets = 'presets'
    legacy = 'legacy'


class Priority(int, Enum):
    preset = 0
    demand = 10
    conversion = 20
    supply = 30
    last = 100


class Investment_production(str, Enum):
    share = 'share'
    match = 'match'


class Demand_share(str, Enum):
    new_and_retro = 'new_and_retro'


class Interactions(str, Enum):
    default = 'default'


class Quantity(str, Enum):
    capacity = 'capacity'


class Sink(str, Enum):
    csv = 'csv'
    netcfd = 'netcfd'
    excel = 'excel'


class Output(BaseModel):
    quantity: Quantity = Quantity.capacity
    sink: Sink = Sink.csv
    filename: str = None

    @validator('filename', pre=True, always=True)
    def validate_filename(cls, value, values):
        if value is None:
            return '{cwd}/{default_output_dir}/{Sector}/'+Quantity+'/{year}'+values.sink
        else:
            return value

    def __init__(self, quantity, sink, filename, overwrite):
        self.quantity = quantity
        self.sink = sink
        self.filename = filename
        self.overwrite = overwrite


class StandardSectors(BaseModel):
    type: Type = Type.default
    priority: Priority = Priority.last
    interpolation: Optional[str] = None
    investment_production: Investment_production = Investment_production.share
    # not really defined so I can't create enum type
    dispatch_production: Optional[str] = None
    demand_share: Demand_share = Demand_share.new_and_retro
    interactions: Interactions = Interactions.default
    timeslices: Dict[str,Any]
    output: Output = None
    # should be path to csv file
    technodata: str = None
    timeslice_levels: List[str] = ["month", "day", "hour"]
    # should be path to csv file
    commodities_in: str = None    
    commodities_out: str = None    
    existing_capacity: str = None    
    agents: str = None


class PresetSectors(BaseModel):
    type: Type = Type.presets
    priority: Priority = Priority.last    
    timeslices_levels:List[str] = ["month", "day", "hour"]
    consumption_path: str = None
    supply_path: str = None
    prices_path: str = None
    demand_path: str = None
    macrodrivers_path: str = None
    regression_path: str = None
    timeslice_shares_path: Optional[str] = None
    filters: Optional[Dict[str,Any]]

class LegacySectors(BaseModel):
    type: Type = Type.legacy
    priority: Priority = Priority.last
    agregation_level: str = None
    excess: int = 0
    timeslices_path: str = None
    userdata_path: str = None
    technodata_path: str = None
    output_path: str = None