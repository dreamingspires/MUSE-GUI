from typing import Dict, List

from muse_gui.data_defs.commodity import Commodity

from .base import BaseBackDependents, BaseDatastore, BaseForwardDependents
from muse_gui.data_defs.region import Region
from .exceptions import KeyAlreadyExists, KeyNotFound
from dataclasses import dataclass

from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from . import Datastore

@dataclass
class RegionBackDependents(BaseBackDependents):
    pass

@dataclass
class RegionForwardDependents(BaseForwardDependents):
    commodities: List[str]
    processes: List[str]
    agents: List[str]

class RegionDatastore(BaseDatastore[Region, RegionBackDependents, RegionForwardDependents]):
    _regions: Dict[str, Region]
    def __init__(self, parent: "Datastore", regions: List[Region] = []) -> None:
        self._regions = {}
        for region in regions:
            self.create(region)
        self._parent = parent

    def create(self, model: Region) -> Region:
        if model.name in self._regions:
            raise KeyAlreadyExists(model.name, self)
        else:
            self._regions[model.name] = model
            return model
    def update(self, key: str, model: Region) -> Region:
        if key not in self._regions:
            raise KeyNotFound(key, self)
        else:
            self._regions[key] = model
            return model
    def read(self, key: str) -> Region:
        if key not in self._regions:
            raise KeyNotFound(key, self)
        else:
            return self._regions[key]

    def delete(self, key: str) -> None:
        self.back_dependents(key)
        raise NotImplementedError
    
    def back_dependents(self, key:str) -> RegionBackDependents:
        return RegionBackDependents()

    def forward_dependents(self, key: str) -> RegionForwardDependents:
        raise NotImplementedError

