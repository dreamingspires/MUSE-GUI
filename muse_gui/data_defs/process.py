from typing import List, Literal

from pydantic import BaseModel, confloat
from pydantic.class_validators import validator
from pydantic.types import NonNegativeInt

from .abstract import Data

Float0To100 = confloat(ge=0, le=100)
Float0To1 = confloat(ge=0, le=1.0)

class CommodityFlow(BaseModel):
    commodity: str
    region:str
    timeslice: str
    level: str
    value: str


class Cost(BaseModel):
    cap_par: float = 0
    cap_exp: float = 1.0
    fix_par: float = 0
    fix_exp: float = 1.0
    var_par: float = 0
    var_exp: float = 1.0
    interest_rate: NonNegativeInt = 0

class Utilisation(BaseModel):
    utilization_factor: Float0To1 = 0
    efficiency: Float0To100 = 0

class Capacity(BaseModel):
    max_capacity_addition: NonNegativeInt = 0
    max_capacity_growth: Float0To100 = 0
    total_capacity_addition: NonNegativeInt = 0
    technical_life: NonNegativeInt = 0
    scaling_size: NonNegativeInt = 0

ZeroToOne = confloat(gt=0.0, le=1.0)

class CapacityShare(BaseModel):
    agent_name: str
    share: ZeroToOne

class Technodata(BaseModel):
    region: str
    time: str
    level: Literal['fixed', 'flexible'] = 'fixed'
    cost: Cost
    utilisation: Utilisation
    capacity: Capacity
    agents: List[CapacityShare]
    @validator('agents')
    def sum_agent_share_to_one(cls,v):
        shares = [agent.share for agent in v]
        if sum(shares) != 1 :
            raise NotImplementedError
        else:
            return v


class ExistingCapacity(BaseModel):
    region: str
    year: int
    value: float


class Process(Data):
    name: str
    sector: str
    fuel: str # Commodity
    end_use: str # Commodity
    type: str
    technodatas: List[Technodata]
    comm_in: List[CommodityFlow]
    comm_out: List[CommodityFlow]
    existing_capacities: List[ExistingCapacity]
    @validator('comm_in')
    def at_least_one_in(cls, v: List[CommodityFlow]):
        if len(v) ==0:
            raise ValueError('At least one comm_in must be supplied')
        else:
            return v

    @validator('comm_out')
    def at_least_one_out(cls, v: List[CommodityFlow]):
        if len(v) ==0:
            raise ValueError('At least one comm_out must be supplied')
        else:
            return v

    @validator('comm_in')
    def contains_fuel(cls, v: List[CommodityFlow], values):
        assert 'fuel' in values
        fuel: str = values['fuel']
        commods = [commod_flow.commodity for commod_flow in v]
        if fuel not in commods:
            raise ValueError(f'Fuel: {fuel} not present in comm_in')
    @validator('comm_out')
    def contains_end_use(cls, v: List[CommodityFlow], values):
        assert 'end_use' in values
        end_use: str = values['end_use']
        commods = [commod_flow.commodity for commod_flow in v]
        if end_use not in commods:
            raise ValueError(f'End use: {end_use} not present in comm_out')
    capacity_unit: str