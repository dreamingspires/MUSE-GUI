from dataclasses import dataclass
from typing import Dict, List

from muse_gui.backend.resources.datastore.base import BaseDatastore
from muse_gui.backend.resources.datastore.exceptions import DependentNotFound, KeyAlreadyExists, KeyNotFound
from muse_gui.data_defs.agent import Agent

from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from . import Datastore


class AgentDatastore(BaseDatastore[Agent]):
    def __init__(self, parent: "Datastore", agents: List[Agent] = []) -> None:
        self._parent = parent
        self._data = {}
        for agent in agents:
            self.create(agent)

    def create(self, model: Agent) -> Agent:
        return super().create(model, model.name)
    
    def update(self, key: str, model: Agent) -> Agent:
        return super().update(key, model.name, model)

    def delete(self, key: str) -> None:
        self._data.pop(key)
        return None

    def back_dependents(self, model: Agent) -> Dict[str,List[str]]:
        try:
            region = self._parent.region.read(model.region)
        except KeyNotFound:
            raise DependentNotFound(model, model.region, self._parent.region)
        regions = [region.name]
        return {
            'region': regions
        }

