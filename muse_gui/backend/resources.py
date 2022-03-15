from typing import Dict, Generic, List, Type, TypeVar

from pydantic.main import BaseModel
from muse_gui.data_defs.region import Region

#########################
#DATATYPES

class Region(BaseModel):
    name: str

################################
#DATASTORE DEF

ModelType = TypeVar("ModelType", bound =BaseModel)
class BaseDatastore(Generic[ModelType]):
    def create(self, model: ModelType) -> ModelType:
        raise NotImplementedError

    def update(self, key: str, model: ModelType) -> ModelType:
        raise NotImplementedError

    def read(self, key: str) -> ModelType:
        raise NotImplementedError

    def delete(self, key: str) -> None:
        raise NotImplementedError

    def dependents(self, key: str):
        raise NotImplementedError

#########################
#EXCEPTIONS
class KeyAlreadyExists(ValueError):
    def __init__(self, key:str, datastore: Type[BaseDatastore]) -> None:
        super().__init__(f"{key} already exists in {datastore.__name__}")

class KeyNotFound(ValueError):
    def __init__(self, key:str, datastore: Type[BaseDatastore]) -> None:
        super().__init__(f"{key} not found in {datastore.__name__}")
################################
#DATASTORES

class RegionDatastore(BaseDatastore[Region]):
    _regions: Dict[str, Region]
    def __init__(self, parent: "Datastore", regions: List[Region] = []) -> None:
        new_regions = {}
        for region in regions:
            if region.name in new_regions:
                raise KeyAlreadyExists(region.name, RegionDatastore)
            else:
                new_regions[region.name] = region
        self._regions = new_regions
        self._parent = parent
    def create(self, model: Region) -> Region:
        if model.name in self._regions:
            raise KeyAlreadyExists(model.name, RegionDatastore)
        else:
            self._regions[model.name] = model
            return model
    def update(self, key: str, model: Region) -> Region:
        if key not in self._regions:
            raise KeyNotFound(key, RegionDatastore)
        else:
            self._regions[key] = model
            return model
    def read(self, key: str) -> Region:
        if key not in self._regions:
            raise KeyNotFound(key, RegionDatastore)
        else:
            return self._regions[key]

    def delete(self, key: str) -> None:
        self.dependents(key)
        raise NotImplementedError

    def dependents(self, key: str):
        raise NotImplementedError


class Datastore:
    _region_datastore: RegionDatastore
    def __init__(self, regions: List[Region] = []) -> None:
        self._region_datastore = RegionDatastore(self, regions)
        pass

    @property
    def region(self):
        return self._region_datastore
    
