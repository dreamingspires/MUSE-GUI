from dataclasses import dataclass
from typing import Dict, List

from muse_gui.backend.resources.datastore.base import BaseDatastore
from muse_gui.backend.resources.datastore.exceptions import KeyAlreadyExists, KeyNotFound
from muse_gui.data_defs.timeslice import LevelName

from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from . import Datastore

class LevelNameDatastore(BaseDatastore[LevelName]):
    def __init__(self, parent: "Datastore", level_names: List[LevelName] = []) -> None:
        self._parent = parent
        self._data = {}
        for level_name in level_names:
            self.create(level_name)

    def create(self, model: LevelName) -> LevelName:
        return super().create(model, model.level)
    
    def update(self, key: str, model: LevelName) -> LevelName:
        return super().update(key, model.level, model)

    def back_dependents(self, model: LevelName) -> Dict[str,List[str]]:
        return {}
    
    def forward_dependents(self, model: LevelName) -> Dict[str,List[str]]:
        timeslices = []
        for key, _ in self._parent.timeslice._data.items():
            timeslices.append(key)
        return {
            'timeslice': timeslices
        }
