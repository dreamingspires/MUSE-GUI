from dataclasses import dataclass
from typing import Dict, List

from muse_gui.backend.resources.datastore.base import BaseBackDependents, BaseDatastore, BaseForwardDependents
from muse_gui.data_defs.timeslice import LevelName


@dataclass
class LevelNameBackDependents(BaseBackDependents):
    pass

@dataclass
class LevelNameForwardDependents(BaseForwardDependents):
    pass

class LevelNameDatastore(BaseDatastore[LevelName, LevelNameBackDependents, LevelNameForwardDependents]):
    _level_names: Dict[str, LevelName]
    def __init__(self) -> None:
        raise NotImplementedError

    def create(self, model: LevelName) -> LevelName:
        raise NotImplementedError
    
    def read(self, key: str) -> LevelName:
        raise NotImplementedError
    
    def update(self, key: str, model: LevelName) -> LevelName:
        raise NotImplementedError

    def delete(self, key: str) -> None:
        raise NotImplementedError
    
    def back_dependents(self, key: str) -> LevelNameBackDependents:
        return LevelNameBackDependents()
    
    def forward_dependents(self, key: str) -> LevelNameForwardDependents:
        raise NotImplementedError
