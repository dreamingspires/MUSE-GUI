from typing import Dict, List

from muse_gui.data_defs.commodity import Commodity

from .base import BaseBackDependents, BaseDatastore, BaseForwardDependents
from muse_gui.data_defs.region import Region
from .exceptions import KeyAlreadyExists, KeyNotFound
from dataclasses import dataclass

from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from . import Datastore

class RegionBackDependents(BaseBackDependents):
    pass

class RegionForwardDependents(BaseForwardDependents):
    commodity: List[str]
    process: List[str]
    agent: List[str]

class RegionDatastore(BaseDatastore[Region, RegionBackDependents, RegionForwardDependents]):
    def __init__(self, parent: "Datastore", regions: List[Region] = []) -> None:
        self._parent = parent
        self._data = {}
        for region in regions:
            self.create(region)


    def create(self, model: Region) -> Region:
        return super().create(model, model.name)

    def update(self, key: str, model: Region) -> Region:
        if key not in self._data:
            raise KeyNotFound(key, self)
        else:
            self._data[key] = model
            return model
    def read(self, key: str) -> Region:
        if key not in self._data:
            raise KeyNotFound(key, self)
        else:
            return self._data[key]

    def delete(self, key: str) -> None:
        existing = self.read(key)
        forward_deps = self.forward_dependents(existing)
        for commodity_key in forward_deps.commodity:
            try:
                self._parent.commodity.delete(commodity_key)
            except KeyNotFound:
                pass
        for process_key in forward_deps.process:
            try:
                self._parent.process.delete(process_key)
            except KeyNotFound:
                pass
        for agent_key in forward_deps.agent:
            try:
                self._parent.agent.delete(agent_key)
            except KeyNotFound:
                pass
        self._data.pop(key)
        return None

    def back_dependents(self, model: Region) -> RegionBackDependents:
        return RegionBackDependents()

    def forward_dependents(self, model: Region) -> RegionForwardDependents:
        commodities = []
        for key, commodity in self._parent.commodity._data.items():
            for price in commodity.commodity_prices.prices:
                if price.region_name == model.name:
                    commodities.append(key)
        processes = []
        for key, process in self._parent.process._data.items():
            if process.region == model.name:
                processes.append(key)
        agents = []
        for key, agent in self._parent.agent._data.items():
            if agent.region == model.name:
                agents.append(key)
        return RegionForwardDependents(
            commodity = commodities, 
            process= processes,
            agent = agents
        )
