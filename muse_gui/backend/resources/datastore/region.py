from typing import Dict, List

from .base import BaseDatastore
from muse_gui.data_defs.region import Region
from .exceptions import KeyAlreadyExists, KeyNotFound

class RegionDatastore(BaseDatastore[Region]):
    _regions: Dict[str, Region]
    def __init__(self, parent, regions: List[Region] = []) -> None:
        new_regions = {}
        for region in regions:
            if region.name in new_regions:
                raise KeyAlreadyExists(region.name, self)
            else:
                new_regions[region.name] = region
        self._regions = new_regions
        self._parent = parent
    def create(self, model: Region) -> Region:
        if model.name in self._regions:
            raise KeyAlreadyExists(model.name, self)
        else:
            self._regions[model.name] = model
            return model
    def update(self, key: str, model: Region) -> Region:
        if key not in self._regions:
            raise KeyNotFound(key, self)
        else:
            self._regions[key] = model
            return model
    def read(self, key: str) -> Region:
        if key not in self._regions:
            raise KeyNotFound(key, self)
        else:
            return self._regions[key]

    def delete(self, key: str) -> None:
        self.dependents(key)
        raise NotImplementedError

    def dependents(self, key: str):
        raise NotImplementedError

