from dataclasses import dataclass
from typing import Dict, List

from muse_gui.backend.resources.datastore.base import BaseDatastore
from muse_gui.backend.resources.datastore.exceptions import KeyAlreadyExists, KeyNotFound
from muse_gui.data_defs.process import Process


from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from . import Datastore

class ProcessDatastore(BaseDatastore[Process]):
    def __init__(self, parent: "Datastore", processes: List[Process] = []) -> None:
        self._parent = parent
        self._data = {}
        for process in processes:
            self.create(process)

    def create(self, model: Process) -> Process:
        return super().create(model, model.name)
    
    def update(self, key: str, model: Process) -> Process:
        return super().update(key, model.name, model)

    def back_dependents(self, model: Process) -> Dict[str,List[str]]:
        # region: List[str]
        # sector: List[str]
        # commodity: List[str]
        raise NotImplementedError
    
    def forward_dependents(self, model: Process) -> Dict[str,List[str]]:
        return {}
