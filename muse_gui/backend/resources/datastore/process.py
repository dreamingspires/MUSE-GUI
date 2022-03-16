from dataclasses import dataclass
from typing import Dict, List

from muse_gui.backend.resources.datastore.base import BaseBackDependents, BaseDatastore, BaseForwardDependents
from muse_gui.backend.resources.datastore.exceptions import KeyAlreadyExists, KeyNotFound
from muse_gui.data_defs.process import Process


from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from . import Datastore

class ProcessBackDependents(BaseBackDependents):
    region: List[str]
    sector: List[str]
    commodity: List[str]

class ProcessForwardDependents(BaseForwardDependents):
    pass

class ProcessDatastore(BaseDatastore[Process, ProcessBackDependents, ProcessForwardDependents]):
    def __init__(self, parent: "Datastore", processes: List[Process] = []) -> None:
        self._parent = parent
        self._data = {}
        for process in processes:
            self.create(process)

    def create(self, model: Process) -> Process:
        return super().create(model, model.name)
    
    def update(self, key: str, model: Process) -> Process:
        return super().update(key, model.name, model)

    def delete(self, key: str) -> None:
        self._data.pop(key)
        return None

    def back_dependents(self, model: Process) -> ProcessBackDependents:
        raise NotImplementedError
    
    def forward_dependents(self, model: Process) -> ProcessForwardDependents:
        return ProcessForwardDependents()
