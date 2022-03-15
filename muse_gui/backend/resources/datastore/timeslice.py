from dataclasses import dataclass
from typing import Dict, List

from .base import BaseBackDependents, BaseDatastore, BaseForwardDependents
from muse_gui.data_defs.timeslice import Timeslice
from .exceptions import KeyAlreadyExists, KeyNotFound

from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from . import Datastore

@dataclass
class TimesliceBackDependents(BaseBackDependents):
    level_names: List[str]

@dataclass
class TimesliceForwardDependents(BaseForwardDependents):
    pass

class TimesliceDatastore(BaseDatastore[Timeslice, TimesliceBackDependents, TimesliceForwardDependents]):
    _timeslices: Dict[str, Timeslice]
    def __init__(self, parent: "Datastore", timeslices: List[Timeslice] = []) -> None:
        self._timeslices = {}
        for timeslice in timeslices:
            self.create(timeslice)
        self._parent = parent

    def create(self, model: Timeslice) -> Timeslice:
        if model.name in self._timeslices:
            raise KeyAlreadyExists(model.name, self)
        else:
            self._timeslices[model.name] = model
            return model
    def update(self, key: str, model: Timeslice) -> Timeslice:
        if key not in self._timeslices:
            raise KeyNotFound(key, self)
        else:
            self._timeslices[key] = model
            return model
    def read(self, key: str) -> Timeslice:
        if key not in self._timeslices:
            raise KeyNotFound(key, self)
        else:
            return self._timeslices[key]

    def delete(self, key: str) -> None:
        self.forward_dependents(key)
        raise NotImplementedError

    def back_dependents(self, key:str) -> TimesliceBackDependents:
        raise NotImplementedError

    def forward_dependents(self, key:str) -> TimesliceForwardDependents:
        raise NotImplementedError

