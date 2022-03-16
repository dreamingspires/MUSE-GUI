from dataclasses import dataclass
from typing import Dict, List

from muse_gui.backend.resources.datastore.base import BaseBackDependents, BaseDatastore, BaseForwardDependents
from muse_gui.backend.resources.datastore.exceptions import KeyAlreadyExists, KeyNotFound
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
    _agents: Dict[str, Agent]
    def __init__(self, parent: "Datastore", agents: List[Agent] = []) -> None:
        self._parent = parent
        self._agents = {}
        for agent in agents:
            self.create(agent)


    def create(self, model: Agent) -> Agent:
        if model.name in self._agents:
            raise KeyAlreadyExists(model.name, self)
        else:
            self.back_dependents(model)
            self._agents[model.name] = model
            return model
    
    def read(self, key: str) -> Agent:
        if key not in self._agents:
            raise KeyNotFound(key, self)
        else:
            return self._agents[key]
    
    def update(self, key: str, model: Agent) -> Agent:
        if key not in self._agents:
            raise KeyNotFound(key, self)
        else:
            existing = self.read(key)
            self.back_dependents(existing)
            self.back_dependents(model)
            self._agents[key] = model
            return model

    def delete(self, key: str) -> None:
        self._agents.pop(key)
        return None
    
    def back_dependents(self, model: Agent) -> AgentBackDependents:
        raise NotImplementedError
    
    def forward_dependents(self, model: Agent) -> AgentForwardDependents:
        return AgentForwardDependents()
