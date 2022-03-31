from enum import Enum
from typing import List, Literal, Optional, Union

from .abstract import Data


class InterpolationType(str, Enum):
    """
    See check_interpolation_mode in [toml.py](https://github.com/SGIModel/MUSE_ICL/blob/856bec4652c50e16413a353b98280024b2e9ddc4/src/muse/readers/toml.py#L688)
    """

    NEAREST = "nearest"
    LINEAR = "linear"
    CUBIC = "cubic"


class Production(str, Enum):
    SHARE = "share"
    COSTED = "costed"


class InvProduction(Data):
    name: Optional[str] = None
    costing: Optional[str] = None


class SectorType(str, Enum):
    STANDARD = "standard"
    PRESET = "preset"


class BaseSector(Data):
    name: str
    priority: int = 100
    type: SectorType


class StandardSector(BaseSector):
    """
    TODO: Advanced Mode
    """

    type: Literal[SectorType.STANDARD] = SectorType.STANDARD
    interpolation: InterpolationType = InterpolationType.LINEAR
    dispatch_production: Production = Production.SHARE
    investment_production: Optional[InvProduction] = None
    forecast: Optional[int] = None
    demand_share: Literal["new_and_retro"] = "new_and_retro"
    lpsolver: Optional[str] = None
    constraints: Optional[List[str]] = None


class PresetSector(BaseSector):
    """
    TODO: Advanced Mode
    """

    type: Literal[SectorType.PRESET] = SectorType.PRESET


Sector = Union[StandardSector, PresetSector]
