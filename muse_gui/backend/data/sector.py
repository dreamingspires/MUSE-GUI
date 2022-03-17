from typing import Annotated, Any, Dict, Literal, Optional, Union
from .abstract import Data
from enum import Enum
from pydantic import Field

class InterpolationType(str, Enum):
    """
    See check_interpolation_mode in [toml.py](https://github.com/SGIModel/MUSE_ICL/blob/856bec4652c50e16413a353b98280024b2e9ddc4/src/muse/readers/toml.py#L688)
    """
    NEAREST = 'nearest'
    LINEAR = 'linear'
    CUBIC = 'cubic'

class Production(str, Enum):
    SHARE = 'share'
    COSTED = 'costed'

class BaseSector(Data):
    name: str
    priority: int = 100

class StandardSector(BaseSector):
    """
    TODO: Advanced Mode
    """
    type: Literal['standard'] = 'standard'
    interpolation: InterpolationType = InterpolationType.LINEAR
    dispatch_production: Production = Production.SHARE
    investment_production: Production = Production.SHARE
    demand_share: Literal['new_and_retro'] = 'new_and_retro'

class PresetSector(BaseSector):
    """
    TODO: Advanced Mode
    """
    type: Literal['preset'] = 'preset'


Sector = Union[StandardSector, PresetSector]