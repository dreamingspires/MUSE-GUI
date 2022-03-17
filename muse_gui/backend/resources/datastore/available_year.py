

from dataclasses import dataclass
from typing import Dict, List

from muse_gui.backend.resources.datastore.base import BaseDatastore
from muse_gui.backend.resources.datastore.exceptions import KeyNotFound
from muse_gui.backend.data.timeslice import AvailableYear

from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from . import Datastore


class AvailableYearDatastore(BaseDatastore[AvailableYear]):
    def __init__(self, parent: "Datastore", available_years: List[AvailableYear] = []) -> None:
        self._parent = parent
        self._data = {}
        for available_year in available_years:
            self.create(available_year)


    def create(self, model: AvailableYear) -> AvailableYear:
        return super().create(model, str(model.year))
    
    def update(self, key: str, model: AvailableYear) -> AvailableYear:
        return super().update(key, str(model.year), model)
    
    def forward_dependents(self, model: AvailableYear) -> Dict[str,List[str]]:
        commodities = []
        for key, commodity in self._parent.commodity._data.items():
            for price in commodity.commodity_prices:
                if price.time == model.year:
                    commodities.append(key)
        return {
            'commodity': list(set(commodities))
        }

