from typing import Dict, Literal

from pydantic import BaseModel, confloat, conint
from pydantic.types import NonNegativeInt
from .abstract import Data, View
from .region import Region
import PySimpleGUI as sg
from PySimpleGUI import Element

Float0To100 = confloat(ge=0, le=100)
Float0To1 = confloat(ge=0, le=1.0)

class Process(Data):
    name: str
    region: Region
    level: Literal['fixed', 'flexible'] = 'fixed'
    type: str
    fuel: str
    end_use: str
    cap_par: float = 0
    cap_exp: float = 1.0
    fix_par: float = 0
    fix_exp: float = 1.0
    var_par: float = 0
    var_exp: float = 1.0
    max_capacity_addition: NonNegativeInt = 0
    max_capacity_growth: Float0To100 = 0
    total_capacity_addition: NonNegativeInt = 0
    technical_life: NonNegativeInt = 0
    utilization_factor: Float0To1 = 0
    efficiency: Float0To100 = 0
    scaling_size: NonNegativeInt = 0
    interest_rate: NonNegativeInt = 0


class ProcessView(View):
    """
    TODO: Fill other values for view
    """
    model: Process

    def item(self) -> Dict[str, Element]:
        return {
            'name': sg.Input(self.model.name),
            'region': sg.Input(self.model.region.name),
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
