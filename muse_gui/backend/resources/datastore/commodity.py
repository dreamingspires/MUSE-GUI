from typing import Dict, List
from muse_gui.backend.resources.datastore import available_year

from muse_gui.backend.resources.datastore.region import RegionDatastore
from muse_gui.data_defs.process import Process
from muse_gui.data_defs.timeslice import AvailableYear

from .base import BaseDatastore
from .exceptions import DependentNotFound, KeyAlreadyExists, KeyNotFound
from muse_gui.data_defs.commodity import Commodity
from muse_gui.data_defs.region import Region
from dataclasses import dataclass
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
        for price in model.commodity_prices.prices:
            try:
                region = self._parent.region.read(price.region_name)
            except KeyNotFound:
                raise DependentNotFound(model, price.region_name, self._parent.region)
            try:
                year = self._parent.available_year.read(str(price.time))
            except KeyNotFound:
                raise DependentNotFound(model, price.region_name, self._parent.region)
            regions.append(region.name)
            available_years.append(str(year.year))
        return {
            'region': regions,
            'available_year': available_years
        }
    
    def forward_dependents(self, model: Commodity) -> Dict[str,List[str]]:
        #process: List[str]
        raise NotImplementedError