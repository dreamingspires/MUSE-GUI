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
    def __init__(self, parent: "Datastore", sectors: List[Sector] = []) -> None:
        self._parent = parent
        self._data = {}
        for sector in sectors:
            self.create(sector)

    def create(self, model: Sector) -> Sector:
        return super().create(model, model.name)

    def update(self, key: str, model: Sector) -> Sector:
        return super().update(key, model.name, model)

    def delete(self, key: str) -> None:
        existing = self.read(key)
        self.forward_dependents(existing)
        raise NotImplementedError

    def back_dependents(self, model: Sector) -> SectorBackDependents:
        return SectorBackDependents()

    def forward_dependents(self, model: Sector) -> SectorForwardDependents:
        raise NotImplementedError

