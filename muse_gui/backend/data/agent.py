import math
from typing import Literal, Optional
from pydantic import validator
from pydantic import BaseModel

from pydantic import NonNegativeFloat
from .abstract import Data
from enum import Enum
import numpy as np

def validate_nan_to_none(cls, v):
    print()
    print('here', v)
    if v == np.NaN:
         return None
    else:
        return v

class AgentType(str, Enum):
    Comfort = 'comfort'
    Efficiency = 'efficiency'
    FixedCosts = 'fixed_costs'
    CapitalCosts = 'capital_costs'
    FuelConsumption = 'fuel_consumption_cost'
    Emission = 'Emission'
    LCOE = 'LCOE'
    NPV = 'NPV'
    EAC = 'EAC'

class AgentObjective(BaseModel):
    objective_type: AgentType = AgentType.LCOE
    objective_data: float
    objective_sort: Optional[bool] = None
    validator('objective_sort', pre=True, always = True, allow_reuse=True)(validate_nan_to_none)



class SearchRule(str, Enum):
    SameEndUse = 'same_enduse'
    All = 'all'
    Similar = 'similar_technology'
    FuelType = 'fueltype'
    Existing = 'existing'
    Maturity = 'maturity'
    NonZeroCapacity = 'currently_referenced_tech'


class DecisionMethod(str, Enum):
    Mean = 'mean'
    WeightedSum = 'weighted_sum'
    Lexical = 'lexo'
    RetroLexical = 'retro_lexo'
    Epsilon = 'epsilon'
    RetroEpsilon = 'retro_epsilon'
    SingleObjective = 'singleObj'


class Agent(Data):
    name: str
    type: Literal['New', 'Retrofit']
    region: str
    objective_1: AgentObjective
    budget: float = math.inf
    share: str = ''
    objective_2: Optional[AgentObjective] = None
    objective_3: Optional[AgentObjective] = None
    search_rule: SearchRule = SearchRule.All
    decision_method: DecisionMethod = DecisionMethod.SingleObjective
    quantity: NonNegativeFloat = 1.0
    maturity_threshold: float = -1.0
