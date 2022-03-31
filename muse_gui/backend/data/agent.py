import math
from enum import Enum
from typing import Dict, List, Optional

import numpy as np
from pydantic import BaseModel, NonNegativeFloat, validator

from .abstract import Data


def validate_nan_to_none(cls, v):
    if v == np.NaN:
        return None
    else:
        return v


class ObjectiveType(str, Enum):
    Comfort = "comfort"
    Efficiency = "efficiency"
    FixedCosts = "fixed_costs"
    CapitalCosts = "capital_costs"
    FuelConsumption = "fuel_consumption_cost"
    Emission = "Emission"
    LCOE = "LCOE"
    NPV = "NPV"
    EAC = "EAC"


class AgentObjective(Data):
    objective_type: ObjectiveType = ObjectiveType.LCOE
    objective_data: float
    objective_sort: Optional[bool] = None
    validator("objective_sort", pre=True, always=True, allow_reuse=True)(
        validate_nan_to_none
    )


class SearchRule(str, Enum):
    SameEndUse = "same_enduse"
    All = "all"
    Similar = "similar_technology"
    FuelType = "fueltype"
    Existing = "existing"
    Maturity = "maturity"
    NonZeroCapacity = "currently_referenced_tech"


class DecisionMethod(str, Enum):
    Mean = "mean"
    WeightedSum = "weighted_sum"
    Lexical = "lexo"
    RetroLexical = "retro_lexo"
    Epsilon = "epsilon"
    RetroEpsilon = "retro_epsilon"
    SingleObjective = "singleObj"


class AgentType(str, Enum):
    New = "New"
    Retrofit = "Retrofit"


class AgentData(Data):
    num: Optional[int] = None
    objective_1: AgentObjective
    budget: float = math.inf
    share: str = ""
    objective_2: Optional[AgentObjective] = None
    objective_3: Optional[AgentObjective] = None
    search_rule: SearchRule = SearchRule.All
    decision_method: DecisionMethod = DecisionMethod.SingleObjective
    quantity: NonNegativeFloat = 1.0
    maturity_threshold: float = -1.0


Region = str


class Agent(Data):
    name: str
    sectors: List[str] = []
    new: Dict[Region, AgentData]
    retrofit: Dict[Region, AgentData]
