from typing import Dict, Literal

from pydantic import BaseModel, confloat, conint
from .abstract import Data
from .region import Region
import PySimpleGUI as sg
from PySimpleGUI import Element


class Technology(BaseModel):
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
    max_capacity_addition: conint(ge=0) = 0
    max_capacity_growth: confloat(ge=0, le=100) = 0
    total_capacity_addition: conint(ge=0) = 0
    technical_life: conint(ge=0) = 0
    utilization_factor: confloat(ge=0, le=1.0) = 0
    efficiency: confloat(ge=0, le=100) = 0
    scaling_size: confloat(ge=0) = 0
    interest_rate: confloat(ge=0) = 0


class TechnologyView(Data):
    """
    TODO: Fill other values for view
    """
    model: Technology

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
