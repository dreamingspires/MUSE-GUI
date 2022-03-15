

from dataclasses import dataclass
from typing import Dict, List

from muse_gui.backend.resources.datastore.base import BaseBackDependents, BaseDatastore, BaseForwardDependents
from muse_gui.data_defs.timeslice import AvailableYear


@dataclass
class AvailableYearBackDependents(BaseBackDependents):
    pass

@dataclass
class AvailableYearForwardDependents(BaseForwardDependents):
    pass

class AvailableYearDatastore(BaseDatastore[AvailableYear, AvailableYearBackDependents, AvailableYearForwardDependents]):
    _available_years: Dict[str, AvailableYear]
    def __init__(self) -> None:
        raise NotImplementedError

    def create(self, model: AvailableYear) -> AvailableYear:
        raise NotImplementedError
    
    def read(self, key: str) -> AvailableYear:
        raise NotImplementedError
    
    def update(self, key: str, model: AvailableYear) -> AvailableYear:
        raise NotImplementedError

    def delete(self, key: str) -> None:
        raise NotImplementedError
    
    def back_dependents(self, key: str) -> AvailableYearBackDependents:
        return AvailableYearBackDependents()
    
    def forward_dependents(self, key: str) -> AvailableYearForwardDependents:
        raise NotImplementedError
