from typing import Dict, List, Literal

from pydantic import BaseModel, confloat, conint
from pydantic.types import NonNegativeInt

from muse_gui.data_defs.sector import Sector
from .abstract import Data, View
from .region import Region
import PySimpleGUI as sg
from PySimpleGUI import Element

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

class Utilisation(BaseModel):
    utilization_factor: Float0To1 = 0

class Capacity(BaseModel):
    max_capacity_addition: NonNegativeInt = 0
    max_capacity_growth: Float0To100 = 0
    total_capacity_addition: NonNegativeInt = 0

class Technodata(BaseModel):
    region: str
    time: str
    level: Literal['fixed', 'flexible'] = 'fixed'
    cost: Cost
    utilisation: Utilisation
    capacity: Capacity


class Process(Data):
    name: str
    sector: str
    technodatas: List[Technodata]
    comm_in: List[CommodityFlow]
    comm_out: List[CommodityFlow]
    type: str
    fuel: str
    end_use: str
    technical_life: NonNegativeInt = 0
    efficiency: Float0To100 = 0
    scaling_size: NonNegativeInt = 0
    interest_rate: NonNegativeInt = 0

"""
class ProcessView(View):
"""
#TODO: Fill other values for view
"""
    model: Process

    def item(self) -> Dict[str, Element]:
        return {
            'name': sg.Input(self.model.name),
            'region': sg.Input(self.model.region),
            'level': sg.DropDown([
                'fixed', 'flexible'
            ], default_value=self.model.level),
            'type': sg.Input(self.model.type),
            'fuel': sg.Input(self.model.fuel),
            'end_use': sg.Input(self.model.end_use)
        }

    @classmethod
    def heading(cls):
        return {
            k: sg.Text(k.replace('_', '').title()) for k in [
                'name',
                'region',
                'level',
                'type',
                'fuel',
                'end_use',
            ]
        }
"""