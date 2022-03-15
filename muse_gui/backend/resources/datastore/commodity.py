from typing import Dict, List

from muse_gui.backend.resources.datastore.region import RegionDatastore

from .base import BaseDatastore
from .exceptions import DependentNotFound, KeyAlreadyExists, KeyNotFound
from muse_gui.data_defs.commodity import Commodity
from muse_gui.data_defs.region import Region
from dataclasses import dataclass

@dataclass
class CommodityDependents:
    regions: Dict[str, Region]

class CommodityDatastore(BaseDatastore[Commodity]):
    _commodities: Dict[str, Commodity]
    def __init__(self, parent, commodities: List[Commodity] = []) -> None:
        new_commodities = {}
        for commodity in commodities:
            if commodity.commodity in new_commodities:
                raise KeyAlreadyExists(commodity.commodity, self)
            else:
                new_commodities[commodity.commodity] = commodity
        self._commodities = new_commodities
        self._parent = parent

    def dependents(self, model: Commodity) -> CommodityDependents:
        regions: Dict[str, Region] = {}
        for price in model.commodity_prices.prices:
            try:
                region = self._parent.region.read(price.region_name)
            except KeyNotFound:
                raise DependentNotFound(model, price.region_name, self._parent.region)
            regions[region.name] = region
        return CommodityDependents(regions)
    
    def create(self, model: Commodity) -> Commodity:
        if model.commodity in self._commodities:
            raise KeyAlreadyExists(model.commodity, self)
        else:
            self.dependents(model)
            self._commodities[model.commodity] = model
            return model
    def update(self, key: str, model: Commodity) -> Commodity:
        if key not in self._commodities:
            raise KeyNotFound(key, self)
        else:
            self._commodities[key] = model
            return model
    def read(self, key: str) -> Commodity:
        if key not in self._commodities:
            raise KeyNotFound(key, self)
        else:
            return self._commodities[key]

    def delete(self, key: str) -> None:
        commodity = self.read(key)

        self.dependents(commodity)
        raise NotImplementedError




