from typing import List, Literal, Optional

from pydantic import BaseModel, confloat
from pydantic.class_validators import root_validator, validator
from pydantic.types import NonNegativeFloat, NonNegativeInt

from muse_gui.backend.data.agent import AgentType

from .abstract import Data

Float0To100 = confloat(ge=0, le=100)
Float0To1 = confloat(ge=0, le=1.0)


class CommodityFlow(BaseModel):
    commodity: str
    region: str
    timeslice: str
    level: str
    value: float


class DemandFlow(BaseModel):
    commodity: str
    region: str
    timeslice: str
    value: float


class Cost(BaseModel):
    cap_par: float = 0
    cap_exp: float = 1.0
    fix_par: float = 0
    fix_exp: float = 1.0
    var_par: float = 0
    var_exp: float = 1.0
    interest_rate: NonNegativeFloat = 0


class Utilisation(BaseModel):
    utilization_factor: Float0To1 = 0
    efficiency: Float0To100 = 0


class Capacity(BaseModel):
    max_capacity_addition: NonNegativeInt = 0
    max_capacity_growth: Float0To100 = 0
    total_capacity_limit: NonNegativeInt = 0
    technical_life: NonNegativeInt = 0
    scaling_size: NonNegativeFloat = 0


ZeroToOne = confloat(gt=0.0, le=1.0)


class CapacityShare(BaseModel):
    agent_name: str
    agent_type: AgentType
    region: str
    share: ZeroToOne


class Technodata(BaseModel):
    region: str
    time: str
    level: Literal["fixed", "flexible"] = "fixed"
    cost: Cost
    utilisation: Utilisation
    capacity: Capacity
    agents: List[CapacityShare]

    @validator("agents")
    def sum_agent_share_to_one(cls, v):
        shares = [agent.share for agent in v]
        if sum(shares) != 1:
            raise NotImplementedError
        else:
            return v


class ExistingCapacity(BaseModel):
    region: str
    year: int
    value: float


class Demand(BaseModel):
    year: int
    demand_flows: List[DemandFlow]


class Process(Data):
    name: str
    sector: str
    preset_sector: Optional[str]
    fuel: str  # Commodity
    end_use: str  # Commodity
    type: str
    technodatas: List[Technodata]
    comm_in: List[CommodityFlow]
    comm_out: List[CommodityFlow]
    demands: List[Demand]
    existing_capacities: List[ExistingCapacity]

    @root_validator
    def at_least_one_in_or_out(cls, values):
        assert "comm_in" in values
        assert "comm_out" in values
        commodity_in: List[CommodityFlow] = values["comm_in"]
        commodity_out: List[CommodityFlow] = values["comm_out"]
        if len(commodity_in) == 0 and len(commodity_out) == 0:
            raise ValueError("At least one comm_in or comm_out must be supplied")
        else:
            return values

    @validator("comm_in")
    def contains_fuel(cls, v: List[CommodityFlow], values):
        assert "fuel" in values
        fuel: str = values["fuel"]
        commods = [commod_flow.commodity for commod_flow in v]
        if fuel not in commods:
            pass  # Is this a condition? Fails on example
            # raise ValueError(f'Fuel: {fuel} not present in comm_in')
        return v

    @validator("comm_out")
    def contains_end_use(cls, v: List[CommodityFlow], values):
        assert "end_use" in values
        end_use: str = values["end_use"]
        commods = [commod_flow.commodity for commod_flow in v]
        if end_use not in commods:
            pass  # Is this a condition? Fails on example
            # raise ValueError(f'End use: {end_use} not present in comm_out')
        return v

    capacity_unit: str
