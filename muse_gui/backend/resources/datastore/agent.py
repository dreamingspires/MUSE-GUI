from typing import Dict, List

from muse_gui.backend.resources.datastore.base import BaseDatastore
from muse_gui.backend.resources.datastore.exceptions import DependentNotFound, KeyNotFound
from muse_gui.backend.data.agent import Agent

from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from . import Datastore


class AgentDatastore(BaseDatastore[Agent]):
    def __init__(self, parent: "Datastore", agents: List[Agent] = []) -> None:
        super().__init__(parent, 'name', data = agents)

    def back_dependents(self, model: Agent) -> Dict[str,List[str]]:
        try:
            region = self._parent.region.read(model.region)
        except KeyNotFound:
            raise DependentNotFound(model, model.region, self._parent.region)
        regions = [region.name]
        return {
            'region': regions
        }

