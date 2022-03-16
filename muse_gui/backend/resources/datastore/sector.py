from dataclasses import dataclass
from typing import Dict, List

from .base import BaseBackDependents, BaseDatastore, BaseForwardDependents
from muse_gui.data_defs.sector import Sector
from .exceptions import KeyAlreadyExists, KeyNotFound

from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from . import Datastore

@dataclass
class SectorBackDependents(BaseBackDependents):
    pass

@dataclass
class SectorForwardDependents(BaseForwardDependents):
    processes: List[str]

class SectorDatastore(BaseDatastore[Sector, SectorBackDependents, SectorForwardDependents]):
    _sectors: Dict[str, Sector]
    def __init__(self, parent: "Datastore", sectors: List[Sector] = []) -> None:
        self._parent = parent
        self._sectors = {}
        for sector in sectors:
            self.create(sector)

    def create(self, model: Sector) -> Sector:
        if model.name in self._sectors:
            raise KeyAlreadyExists(model.name, self)
        else:
            self._sectors[model.name] = model
            return model
    def update(self, key: str, model: Sector) -> Sector:
        if key not in self._sectors:
            raise KeyNotFound(key, self)
        else:
            self._sectors[key] = model
            return model
    def read(self, key: str) -> Sector:
        if key not in self._sectors:
            raise KeyNotFound(key, self)
        else:
            return self._sectors[key]

    def delete(self, key: str) -> None:
        existing = self.read(key)
        self.forward_dependents(existing)
        raise NotImplementedError

    def back_dependents(self, model: Sector) -> SectorBackDependents:
        return SectorBackDependents()

    def forward_dependents(self, model: Sector) -> SectorForwardDependents:
        raise NotImplementedError

