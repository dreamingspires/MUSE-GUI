from dataclasses import dataclass
from typing import Dict, List

from .base import BaseBackDependents, BaseDatastore, BaseForwardDependents
from muse_gui.data_defs.sector import Sector
from .exceptions import KeyAlreadyExists, KeyNotFound

from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from . import Datastore

class SectorBackDependents(BaseBackDependents):
    pass

class SectorForwardDependents(BaseForwardDependents):
    process: List[str]

class SectorDatastore(BaseDatastore[Sector, SectorBackDependents, SectorForwardDependents]):
    _data: Dict[str, Sector]
    def __init__(self, parent: "Datastore", sectors: List[Sector] = []) -> None:
        self._parent = parent
        self._data = {}
        for sector in sectors:
            self.create(sector)

    def create(self, model: Sector) -> Sector:
        if model.name in self._data:
            raise KeyAlreadyExists(model.name, self)
        else:
            self._data[model.name] = model
            return model
    def update(self, key: str, model: Sector) -> Sector:
        if key not in self._data:
            raise KeyNotFound(key, self)
        else:
            self._data[key] = model
            return model
    def read(self, key: str) -> Sector:
        if key not in self._data:
            raise KeyNotFound(key, self)
        else:
            return self._data[key]

    def delete(self, key: str) -> None:
        existing = self.read(key)
        self.forward_dependents(existing)
        raise NotImplementedError

    def list(self) -> List[str]:
        return list(self._data.keys())

    def back_dependents(self, model: Sector) -> SectorBackDependents:
        return SectorBackDependents()

    def forward_dependents(self, model: Sector) -> SectorForwardDependents:
        raise NotImplementedError

