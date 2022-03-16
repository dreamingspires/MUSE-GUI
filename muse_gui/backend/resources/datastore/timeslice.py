from dataclasses import dataclass
from typing import Dict, List

from .base import BaseBackDependents, BaseDatastore, BaseForwardDependents
from muse_gui.data_defs.timeslice import Timeslice
from .exceptions import KeyAlreadyExists, KeyNotFound, LevelNameMismatch

from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from . import Datastore

class TimesliceBackDependents(BaseBackDependents):
    level_name: List[str]

class TimesliceForwardDependents(BaseForwardDependents):
    pass

class TimesliceDatastore(BaseDatastore[Timeslice, TimesliceBackDependents, TimesliceForwardDependents]):
    _timeslices: Dict[str, Timeslice]
    _parent: "Datastore"
    def __init__(self, parent: "Datastore", timeslices: List[Timeslice] = []) -> None:
        self._parent = parent
        self._timeslices = {}
        for timeslice in timeslices:
            self.create(timeslice)

    def create(self, model: Timeslice) -> Timeslice:
        if model.name in self._timeslices:
            raise KeyAlreadyExists(model.name, self)
        else:

            self.back_dependents(model)
            self._timeslices[model.name] = model
            return model
    def update(self, key: str, model: Timeslice) -> Timeslice:
        if key not in self._timeslices:
            raise KeyNotFound(key, self)
        else:
            existing = self.read(key)
            self.back_dependents(existing)
            self.back_dependents(model)
            self._timeslices[key] = model
            return model
    def read(self, key: str) -> Timeslice:
        if key not in self._timeslices:
            raise KeyNotFound(key, self)
        else:
            return self._timeslices[key]

    def delete(self, key: str) -> None:
        self._timeslices.pop(key)
        return None
    
    def list(self) -> List[str]:
        return list(self._timeslices.keys())
    
    def back_dependents(self, model: Timeslice) -> TimesliceBackDependents:
        level_names = self._parent.level_name.list()
        provided_levels = model.name.split('.')
        if len(level_names) != len(provided_levels):
            raise LevelNameMismatch(level_names, provided_levels)
        else:
            return TimesliceBackDependents(level_name = level_names)

    def forward_dependents(self, model: Timeslice) -> TimesliceForwardDependents:
        return TimesliceForwardDependents()
