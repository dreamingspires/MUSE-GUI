import math
from typing import Dict, Literal, Optional

from pydantic import BaseModel, confloat
from pydantic.types import PositiveFloat
from .abstract import Data
from .region import Region
import PySimpleGUI as sg
from PySimpleGUI import Element
from enum import Enum


class AgentObjective(str, Enum):
    Comfort = 'comfort'
    Efficiency = 'efficiency'
    FixedCosts = 'fixed_costs'
    CapitalCosts = 'capital_costs'
    FuelConsumption = 'fuel_consumption_cost'
    Emission = 'Emission'
    LCOE = 'LCOE'
    NPV = 'NPV'
    EAC = 'EAC'


class SearchRule(str, Enum):
    SameEndUse = 'same_enduse'
    All = 'All'
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
    SingleObjective = 'single_objective'


class Agent(BaseModel):
    name: str
    type: Literal['New', 'Retrofit']
    region: Region
    objective_1: AgentObjective = AgentObjective.LCOE
    budget: float = math.inf
    share: str = ''
    objective_2: Optional[AgentObjective] = None
    objective_3: Optional[AgentObjective] = None
    search_rule: SearchRule = SearchRule.All
    decision_method: DecisionMethod = DecisionMethod.SingleObjective
    quantity: PositiveFloat = 1.0
    maturity_threshold: float = -1.0


class AgentView(Data):
    model: Agent

    def item(self):
        return {
            'name': sg.Input(self.model.name),
            'type': sg.DropDown([
                'New', 'Retrofit'
            ], default_value=self.model.type),
            'region': sg.Input(self.model.region.name),
            'objective': sg.DropDown([
                x.name for x in AgentObjective
            ], default_value=self.model.objective_1.name),
            'budget': sg.Input(self.model.budget),
        }

    @classmethod
    def heading(cls) -> Dict[str, Element]:
        return {
            k: sg.Text(k.title()) for k in [
                'name',
                'type',
                'region',
                'objective',
                'budget'
            ]
        }
