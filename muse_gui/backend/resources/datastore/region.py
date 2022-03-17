from typing import Dict, List

from muse_gui.data_defs.commodity import Commodity

from .base import BaseDatastore
from muse_gui.data_defs.region import Region
from .exceptions import KeyAlreadyExists, KeyNotFound
from dataclasses import dataclass

from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from . import Datastore

class RegionDatastore(BaseDatastore[Region]):
    def __init__(self, parent: "Datastore", regions: List[Region] = []) -> None:
        self._parent = parent
        self._data = {}
        for region in regions:
            self.create(region)

    def create(self, model: Region) -> Region:
        return super().create(model, model.name)

    def update(self, key: str, model: Region) -> Region:
        return super().update(key, model.name, model)

    def forward_dependents(self, model: Region) -> Dict[str,List[str]]:
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
            if agent.region == model.name:
                agents.append(key)
        return {
            'commodity': list(set(commodities)),
            'process': list(set(processes)),
            'agent': list(set(agents))
        }
