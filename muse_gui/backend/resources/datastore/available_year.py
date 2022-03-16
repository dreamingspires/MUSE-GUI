

from dataclasses import dataclass
from typing import Dict, List

from muse_gui.backend.resources.datastore.base import BaseBackDependents, BaseDatastore, BaseForwardDependents
from muse_gui.backend.resources.datastore.exceptions import KeyAlreadyExists, KeyNotFound
from muse_gui.data_defs.timeslice import AvailableYear

from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from . import Datastore

class AvailableYearBackDependents(BaseBackDependents):
    pass

class AvailableYearForwardDependents(BaseForwardDependents):
    commodity: List[str]

class AvailableYearDatastore(BaseDatastore[AvailableYear, AvailableYearBackDependents, AvailableYearForwardDependents]):
    _data: Dict[str, AvailableYear]
    def __init__(self, parent: "Datastore", available_years: List[AvailableYear] = []) -> None:
        self._parent = parent
        self._data = {}
        for available_year in available_years:
            self.create(available_year)


    def create(self, model: AvailableYear) -> AvailableYear:
        if model.year in self._data:
            raise KeyAlreadyExists(str(model.year), self)
        else:
            self._data[str(model.year)] = model
            return model
    
    def read(self, key: str) -> AvailableYear:
        if str(key) not in self._data:
            raise KeyNotFound(str(key), self)
        else:
            return self._data[key]
    
    def update(self, key: str, model: AvailableYear) -> AvailableYear:
        if key not in self._data:
            raise KeyNotFound(str(key), self)
        else:
            self._data[str(key)] = model
            return model

    def delete(self, key: str) -> None:
        existing = self.read(key)
        forward_deps = self.forward_dependents(existing)
        for commodity_key in forward_deps.commodity:
            try:
                self._parent.commodity.delete(commodity_key)
            except KeyNotFound:
                pass
        self._data.pop(key)
        return None


    def list(self) -> List[str]:
        return list(self._data.keys())

    def back_dependents(self, model: AvailableYear) -> AvailableYearBackDependents:
        return AvailableYearBackDependents()
    
    def forward_dependents(self, model: AvailableYear) -> AvailableYearForwardDependents:
        commodities = []
        for key, commodity in self._parent.commodity._data.items():
            for price in commodity.commodity_prices.prices:
                if price.time == model.year:
                    commodities.append(key)
        return AvailableYearForwardDependents(
            commodity = commodities
        )

