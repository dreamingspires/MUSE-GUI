from typing import TYPE_CHECKING, Dict, List

from muse_gui.backend.data.timeslice import Timeslice

from .base import BaseDatastore
from .exceptions import LevelNameMismatch

if TYPE_CHECKING:
    from . import Datastore


class TimesliceDatastore(BaseDatastore[Timeslice]):
    def __init__(self, parent: "Datastore", timeslices: List[Timeslice] = []) -> None:
        super().__init__(parent, "name", data=timeslices)

    def back_dependents(self, model: Timeslice) -> Dict[str, List[str]]:
        level_names = self._parent.level_name.list()
        provided_levels = model.name.split(".")
        if len(level_names) != len(provided_levels):
            raise LevelNameMismatch(level_names, provided_levels)
        else:
            return {"level_name": list(set(level_names))}
