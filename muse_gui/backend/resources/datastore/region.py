from typing import TYPE_CHECKING, Dict, List

from muse_gui.backend.data.region import Region

from .base import BaseDatastore

if TYPE_CHECKING:
    from . import Datastore


class RegionDatastore(BaseDatastore[Region]):
    def __init__(self, parent: "Datastore", regions: List[Region] = []) -> None:
        super().__init__(parent, "name", data=regions)

    def forward_dependents(self, model: Region) -> Dict[str, List[str]]:
        commodities = []
        for key, commodity in self._parent.commodity._data.items():
            for price in commodity.commodity_prices:
                if price.region_name == model.name:
                    commodities.append(key)
        processes = []
        for key, process in self._parent.process._data.items():
            for technodata in process.technodatas:
                if technodata.region == model.name:
                    processes.append(key)
        agents = []
        for key, agent in self._parent.agent._data.items():
            for region, data in agent.new.items():
                if region == model.name:
                    agents.append(key)
            for region, data in agent.retrofit.items():
                if region == model.name:
                    agents.append(key)
        return {
            "commodity": list(set(commodities)),
            "process": list(set(processes)),
            "agent": list(set(agents)),
        }
