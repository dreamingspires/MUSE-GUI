from dataclasses import dataclass
from typing import Dict, List

from muse_gui.backend.resources.datastore.base import BaseBackDependents, BaseDatastore, BaseForwardDependents
from muse_gui.data_defs.process import Process


from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from . import Datastore

@dataclass
class ProcessBackDependents(BaseBackDependents):
    regions: List[str]
    sectors: List[str]
    commodities: List[str]
    available_years: List[str]

@dataclass
class ProcessForwardDependents(BaseForwardDependents):
    pass

class ProcessDatastore(BaseDatastore[Process, ProcessBackDependents, ProcessForwardDependents]):
    _processes: Dict[str, Process]
    def __init__(self, parent: "Datastore", processes: List[Process] = []) -> None:
        self._processes = {}
        for process in processes:
            self.create(process)
        self._parent = parent


    def create(self, model: Process) -> Process:
        raise NotImplementedError
    
    def read(self, key: str) -> Process:
        raise NotImplementedError
    
    def update(self, key: str, model: Process) -> Process:
        raise NotImplementedError

    def delete(self, key: str) -> None:
        raise NotImplementedError
    
    def back_dependents(self, key: str) -> ProcessBackDependents:
        raise NotImplementedError
    
    def forward_dependents(self, key: str) -> ProcessForwardDependents:
        return ProcessForwardDependents()
