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
    _data: Dict[str, LevelName]
    def __init__(self, parent: "Datastore", level_names: List[LevelName] = []) -> None:
        self._parent = parent
        self._data = {}
        for level_name in level_names:
            self.create(level_name)

    def create(self, model: LevelName) -> LevelName:
        if model.level in self._data:
            raise KeyAlreadyExists(model.level, self)
        else:
            self._data[model.level] = model
            return model
    
    def read(self, key: str) -> LevelName:
        if key not in self._data:
            raise KeyNotFound(str(key), self)
        else:
            return LevelName(level=key)
    
    def update(self, key: str, model: LevelName) -> LevelName:
        if key not in self._data:
            raise KeyNotFound(str(key), self)
        else:
            self._data[key] = model
            return model

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

    def list(self) -> List[str]:
        return list(self._data.keys())

    def back_dependents(self, model: LevelName) -> LevelNameBackDependents:
        return LevelNameBackDependents()
    
    def forward_dependents(self, model: LevelName) -> LevelNameForwardDependents:
        timeslices = []
        for key, _ in self._parent.timeslice._data.items():
            timeslices.append(key)
        return LevelNameForwardDependents(
            timeslice = timeslices
        )
