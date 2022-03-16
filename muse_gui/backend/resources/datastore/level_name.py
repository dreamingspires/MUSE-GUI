from dataclasses import dataclass
from typing import Dict, List

from muse_gui.backend.resources.datastore.base import BaseBackDependents, BaseDatastore, BaseForwardDependents
from muse_gui.backend.resources.datastore.exceptions import KeyAlreadyExists, KeyNotFound
from muse_gui.data_defs.timeslice import LevelName

from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from . import Datastore

class LevelNameBackDependents(BaseBackDependents):
    pass

class LevelNameForwardDependents(BaseForwardDependents):
    timeslice: List[str]

class LevelNameDatastore(BaseDatastore[LevelName, LevelNameBackDependents, LevelNameForwardDependents]):
    def __init__(self, parent: "Datastore", level_names: List[LevelName] = []) -> None:
        self._parent = parent
        self._data = {}
        for level_name in level_names:
            self.create(level_name)

    def create(self, model: LevelName) -> LevelName:
        return super().create(model, model.level)
    
    def update(self, key: str, model: LevelName) -> LevelName:
        return super().update(key, model.level, model)

    def delete(self, key: str) -> None:
        existing = self.read(key)
        forward_deps = self.forward_dependents(existing)
        for timeslice_key in forward_deps.timeslice:
            try:
                self._parent.timeslice.delete(timeslice_key)
            except KeyNotFound:
                pass
        self._data.pop(key)
        return None

    def back_dependents(self, model: LevelName) -> LevelNameBackDependents:
        return LevelNameBackDependents()
    
    def forward_dependents(self, model: LevelName) -> LevelNameForwardDependents:
        timeslices = []
        for key, _ in self._parent.timeslice._data.items():
            timeslices.append(key)
        return LevelNameForwardDependents(
            timeslice = timeslices
        )
