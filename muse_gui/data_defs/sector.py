from typing import Dict

from pydantic import BaseModel
from .abstract import Data
import PySimpleGUI as sg
from PySimpleGUI import Element
from enum import Enum


class SectorType(str, Enum):
    '''
    Sector Type
    TODO:
    We are only supporting these.
    If someone extends muse and adds
    sector types, we don't detect those
    See: https://museenergydocs.readthedocs.io/en/latest/inputs/toml.html#standard-sectors
    '''
    DEFAULT = 'default'
    PRESETS = 'presets'


class InterpolationType(str, Enum):
    """
    See check_interpolation_mode in [toml.py](https://github.com/SGIModel/MUSE_ICL/blob/856bec4652c50e16413a353b98280024b2e9ddc4/src/muse/readers/toml.py#L688)
    """
    NEAREST = 'nearest'
    LINEAR = 'linear'
    CUBIC = 'cubic'


class Sector(BaseModel):
    """
    TODO: Advanced Mode
    """
    name: str
    type: SectorType = SectorType.DEFAULT
    priority: int = 100
    interpolation: InterpolationType = InterpolationType.LINEAR
    dispatch_production = 'share'
    investment_production = 'share'
    demand_share = 'new_and_retro'


class SectorView(Data):
    model: Sector

    def item(self) -> Dict[str, Element]:
        return {
            'name': sg.Input(self.model.name),
            'type': sg.DropDown([
                x.name for x in SectorType
            ], default_value=self.model.type.name),
            'priority': sg.Input(self.model.priority),
            'interpolation': sg.DropDown([
                x.name for x in InterpolationType
            ], default_value=self.model.interpolation.name),
        }

    @classmethod
    def heading(cls) -> Dict[str, Element]:
        return {
            k: sg.Text(k.title()) for k in [
                'name',
                'type',
                'priority',
                'interpolation',
            ]
        }
