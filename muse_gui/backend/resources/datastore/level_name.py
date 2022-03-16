from dataclasses import dataclass
from typing import Dict, List

from muse_gui.backend.resources.datastore.base import BaseBackDependents, BaseDatastore, BaseForwardDependents
from muse_gui.backend.resources.datastore.exceptions import KeyAlreadyExists, KeyNotFound
from muse_gui.data_defs.timeslice import LevelName

from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from . import Datastore

@dataclass
class LevelNameBackDependents(BaseBackDependents):
    pass

@dataclass
class LevelNameForwardDependents(BaseForwardDependents):
    timeslices: List[str]

class LevelNameDatastore(BaseDatastore[LevelName, LevelNameBackDependents, LevelNameForwardDependents]):
    _level_names: Dict[str, LevelName]
    def __init__(self, parent: "Datastore", level_names: List[LevelName] = []) -> None:
        self._parent = parent
        self._level_names = {}
        for level_name in level_names:
            self.create(level_name)

    def create(self, model: LevelName) -> LevelName:
        if model.level in self._level_names:
            raise KeyAlreadyExists(model.level, self)
        else:
            self._level_names[model.level] = model
            return model
    
    def read(self, key: str) -> LevelName:
        if key not in self._level_names:
            raise KeyNotFound(str(key), self)
        else:
            return LevelName(level=key)
    
    def update(self, key: str, model: LevelName) -> LevelName:
        if key not in self._level_names:
            raise KeyNotFound(str(key), self)
        else:
            self._level_names[key] = model
            return model

    def delete(self, key: str) -> None:
        raise NotImplementedError
    
    def back_dependents(self, model: LevelName) -> LevelNameBackDependents:
        return LevelNameBackDependents()
    
    def forward_dependents(self, model: LevelName) -> LevelNameForwardDependents:
        raise NotImplementedError
