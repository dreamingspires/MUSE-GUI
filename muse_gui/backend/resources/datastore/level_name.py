from typing import TYPE_CHECKING, Dict, List

from muse_gui.backend.data.timeslice import LevelName
from muse_gui.backend.resources.datastore.base import BaseDatastore

if TYPE_CHECKING:
    from . import Datastore


class LevelNameDatastore(BaseDatastore[LevelName]):
    def __init__(self, parent: "Datastore", level_names: List[LevelName] = []) -> None:
        super().__init__(parent, "level", data=level_names)

    def forward_dependents(self, model: LevelName) -> Dict[str, List[str]]:
        timeslices = []
        for key, _ in self._parent.timeslice._data.items():
            timeslices.append(key)
        return {"timeslice": list(set(timeslices))}
