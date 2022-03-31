from typing import TYPE_CHECKING, Dict, List

from muse_gui.backend.data.sector import PresetSector, Sector, StandardSector

from .base import BaseDatastore

if TYPE_CHECKING:
    from . import Datastore


class SectorDatastore(BaseDatastore[Sector]):
    def __init__(self, parent: "Datastore", sectors: List[Sector] = []) -> None:
        super().__init__(parent, "name", data=sectors)

    def forward_dependents(self, model: Sector) -> Dict[str, List[str]]:
        processes = []
        for key, process in self._parent.process._data.items():
            if process.sector == model.name:
                processes.append(key)
            elif process.preset_sector == model.name:
                processes.append(key)
        agents = []
        for key, agent in self._parent.agent._data.items():
            if model.name in agent.sectors:
                agents.append(key)
        return {"process": list(set(processes)), "agent": list(set(agents))}
