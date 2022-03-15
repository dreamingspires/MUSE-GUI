from dataclasses import dataclass
from typing import Dict, List

from muse_gui.backend.resources.datastore.base import BaseBackDependents, BaseDatastore, BaseForwardDependents
from muse_gui.data_defs.agent import Agent

from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from . import Datastore

@dataclass
class AgentBackDependents(BaseBackDependents):
    regions: List[str]

@dataclass
class AgentForwardDependents(BaseForwardDependents):
    pass

class AgentDatastore(BaseDatastore[Agent, AgentBackDependents, AgentForwardDependents]):
    _processes: Dict[str, Agent]
    def __init__(self, parent: Datastore, agents: List[Agent] = []) -> None:
        raise NotImplementedError

    def create(self, model: Agent) -> Agent:
        raise NotImplementedError
    
    def read(self, key: str) -> Agent:
        raise NotImplementedError
    
    def update(self, key: str, model: Agent) -> Agent:
        raise NotImplementedError

    def delete(self, key: str) -> None:
        raise NotImplementedError
    
    def back_dependents(self, key: str) -> AgentBackDependents:
        raise NotImplementedError
    
    def forward_dependents(self, key: str) -> AgentForwardDependents:
        return AgentForwardDependents()
