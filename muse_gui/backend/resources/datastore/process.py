from dataclasses import dataclass
from typing import Dict, List

from muse_gui.backend.resources.datastore.base import BaseBackDependents, BaseDatastore, BaseForwardDependents
from muse_gui.data_defs.process import Process


@dataclass
class ProcessBackDependents(BaseBackDependents):
    regions: List[str]
    sectors: List[str]
    commodities: List[str]
    available_years: List[str]

@dataclass
class ProcessForwardDependents(BaseForwardDependents):
    #agents: List[str]
    pass

class ProcessDatastore(BaseDatastore[Process, ProcessBackDependents, ProcessForwardDependents]):
    _processes: Dict[str, Process]
    def __init__(self) -> None:
        raise NotImplementedError

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
