from typing import TYPE_CHECKING, Dict, List

from muse_gui.backend.data.agent import Agent
from muse_gui.backend.resources.datastore.base import BaseDatastore
from muse_gui.backend.resources.datastore.exceptions import (
    DependentNotFound,
    KeyNotFound,
)

if TYPE_CHECKING:
    from . import Datastore


class AgentDatastore(BaseDatastore[Agent]):
    def __init__(self, parent: "Datastore", agents: List[Agent] = []) -> None:
        super().__init__(parent, "name", data=agents)

    def back_dependents(self, model: Agent) -> Dict[str, List[str]]:
        regions = []
        for region, data in model.new.items():
            try:
                region_model = self._parent.region.read(region)
            except KeyNotFound:
                raise DependentNotFound(model, region, self._parent.region)
            regions.append(region_model.name)

        sectors = []
        for sector in model.sectors:
            try:
                sector = self._parent.sector.read(sector)
            except KeyNotFound:
                raise DependentNotFound(model, sector, self._parent.sector)
            sectors.append(sector)
        return {"region": regions, "sector": sectors}

    def forward_dependents(self, model: Agent) -> Dict[str, List[str]]:
        processes = []
        for key, process in self._parent.process._data.items():
            for technodata in process.technodatas:
                for agent in technodata.agents:
                    if agent.agent_name == model.name:
                        processes.append(key)
        return {"process": processes}
