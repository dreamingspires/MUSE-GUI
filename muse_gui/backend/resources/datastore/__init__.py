from typing import List

from muse_gui.data_defs.region import Region
from muse_gui.data_defs.commodity import Commodity
from .region import RegionDatastore

class Datastore:
    _region_datastore: RegionDatastore
    def __init__(self, regions: List[Region] = []) -> None:
        self._region_datastore = RegionDatastore(self, regions)
        pass

    @property
    def region(self):
        return self._region_datastore
    
