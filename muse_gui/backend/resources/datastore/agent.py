from dataclasses import dataclass
from typing import Dict, List

from muse_gui.backend.resources.datastore.base import BaseBackDependents, BaseDatastore, BaseForwardDependents
from muse_gui.data_defs.process import Process


@dataclass
class AgentBackDependents(BaseBackDependents):
    regions: List[str]
    #processes: List[str]

@dataclass
class AgentForwardDependents(BaseForwardDependents):
    pass

class ProcessDatastore(BaseDatastore[Process, AgentBackDependents, AgentForwardDependents]):
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
    
    def back_dependents(self, key: str) -> AgentBackDependents:
        raise NotImplementedError
    
    def forward_dependents(self, key: str) -> AgentForwardDependents:
        return AgentForwardDependents()
