

from dataclasses import dataclass
from typing import Dict, List

from muse_gui.backend.resources.datastore.base import BaseBackDependents, BaseDatastore, BaseForwardDependents
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
    _available_years: Dict[str, AvailableYear]
    def __init__(self, parent: "Datastore", available_years: List[AvailableYear] = []) -> None:
        self.available_years = {}
        for available_year in available_years:
            self.create(available_year)
        self._parent = parent


    def create(self, model: AvailableYear) -> AvailableYear:
        raise NotImplementedError
    
    def read(self, key: int) -> AvailableYear:
        raise NotImplementedError
    
    def update(self, key: str, model: AvailableYear) -> AvailableYear:
        raise NotImplementedError

    def delete(self, key: str) -> None:
        raise NotImplementedError
    
    def back_dependents(self, key: str) -> AvailableYearBackDependents:
        return AvailableYearBackDependents()
    
    def forward_dependents(self, key: str) -> AvailableYearForwardDependents:
        raise NotImplementedError
