from typing import Dict, List
from .base import BaseDatastore
from .exceptions import DependentNotFound, KeyNotFound
from muse_gui.backend.data.commodity import Commodity

from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from . import Datastore

class CommodityDatastore(BaseDatastore[Commodity]):
    def __init__(self, parent: "Datastore", commodities: List[Commodity] = []) -> None:
        self._parent = parent
        self._data = {}
        for commodity in commodities:
            self.create(commodity)
    
    def create(self, model: Commodity) -> Commodity:
        return super().create(model, model.commodity)

    def update(self, key: str, model: Commodity) -> Commodity:
        return super().update(key, model.commodity, model)

    def back_dependents(self, model: Commodity) -> Dict[str,List[str]]:
        regions: List[str] = []
        available_years: List[str] = []
        for price in model.commodity_prices:
            try:
                region = self._parent.region.read(price.region_name)
            except KeyNotFound:
                raise DependentNotFound(model, price.region_name, self._parent.region)
            try:
                year = self._parent.available_year.read(str(price.time))
            except KeyNotFound:
                raise DependentNotFound(model, price.time, self._parent.available_year)
            regions.append(region.name)
            available_years.append(str(year.year))
        return {
            'region': list(set(regions)),
            'available_year': list(set(available_years))
        }
    
    def forward_dependents(self, model: Commodity) -> Dict[str,List[str]]:
        processes = []
        for key, process in self._parent.process._data.items():
            for comm_in in process.comm_in:
                if comm_in.commodity == model.commodity:
                    processes.append(key)
            for comm_out in process.comm_in:
                if comm_out.commodity == model.commodity:
                    processes.append(key)
        return {
            'process': list(set(processes))
        }
