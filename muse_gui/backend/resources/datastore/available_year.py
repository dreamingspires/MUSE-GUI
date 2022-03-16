

from dataclasses import dataclass
from typing import Dict, List

from muse_gui.backend.resources.datastore.base import BaseBackDependents, BaseDatastore, BaseForwardDependents
from muse_gui.backend.resources.datastore.exceptions import KeyAlreadyExists, KeyNotFound
from muse_gui.data_defs.timeslice import AvailableYear

from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from . import Datastore

@dataclass
class AvailableYearBackDependents(BaseBackDependents):
    pass

@dataclass
class AvailableYearForwardDependents(BaseForwardDependents):
    commodities: List[str]
    processes: List[str]

class AvailableYearDatastore(BaseDatastore[AvailableYear, AvailableYearBackDependents, AvailableYearForwardDependents]):
    _available_years: Dict[int, AvailableYear]
    def __init__(self, parent: "Datastore", available_years: List[AvailableYear] = []) -> None:
        self._parent = parent
        self._available_years = {}
        for available_year in available_years:
            self.create(available_year)


    def create(self, model: AvailableYear) -> AvailableYear:
        if model.year in self._available_years:
            raise KeyAlreadyExists(str(model.year), self)
        else:
            self._available_years[model.year] = model
            return model
    
    def read(self, key: int) -> AvailableYear:
        if str(key) not in self._available_years:
            raise KeyNotFound(str(key), self)
        else:
            return AvailableYear(year=key)
    
    def update(self, key: int, model: AvailableYear) -> AvailableYear:
        if key not in self._available_years:
            raise KeyNotFound(str(key), self)
        else:
            self._available_years[key] = model
            return model
    def delete(self, key: str) -> None:
        raise NotImplementedError
    
    def back_dependents(self, model: AvailableYear) -> AvailableYearBackDependents:
        return AvailableYearBackDependents()
    
    def forward_dependents(self, model: AvailableYear) -> AvailableYearForwardDependents:
        raise NotImplementedError
