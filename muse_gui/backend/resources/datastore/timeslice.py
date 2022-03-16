from dataclasses import dataclass
from typing import Dict, List

from .base import BaseDatastore
from muse_gui.data_defs.timeslice import Timeslice
from .exceptions import KeyAlreadyExists, KeyNotFound, LevelNameMismatch

from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from . import Datastore

class TimesliceDatastore(BaseDatastore[Timeslice]):
    def __init__(self, parent: "Datastore", timeslices: List[Timeslice] = []) -> None:
        self._parent = parent
        self._data = {}
        for timeslice in timeslices:
            self.create(timeslice)

    def create(self, model: Timeslice) -> Timeslice:
        return super().create(model, model.name)

    def update(self, key: str, model: Timeslice) -> Timeslice:
        return super().update(key, model.name, model)
    
    def back_dependents(self, model: Timeslice) -> Dict[str,List[str]]:
        level_names = self._parent.level_name.list()
        provided_levels = model.name.split('.')
        if len(level_names) != len(provided_levels):
            raise LevelNameMismatch(level_names, provided_levels)
        else:
            return {'level_name': list(set(level_names))}
