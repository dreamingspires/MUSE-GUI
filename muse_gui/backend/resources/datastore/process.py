from dataclasses import dataclass
from typing import Dict, List

from muse_gui.backend.resources.datastore.base import BaseDatastore
from muse_gui.backend.resources.datastore.exceptions import DependentNotFound, KeyAlreadyExists, KeyNotFound
from muse_gui.data_defs.process import Process

from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from . import Datastore

class ProcessDatastore(BaseDatastore[Process]):
    def __init__(self, parent: "Datastore", processes: List[Process] = []) -> None:
        self._parent = parent
        self._data = {}
        for process in processes:
            self.create(process)

    def create(self, model: Process) -> Process:
        return super().create(model, model.name)
    
    def update(self, key: str, model: Process) -> Process:
        return super().update(key, model.name, model)

    def back_dependents(self, model: Process) -> Dict[str,List[str]]:
        commodities: List[str] = []
        regions: List[str] = []
        sectors: List[str] = []       

        for technodata in model.technodatas:
            try:
                region = self._parent.region.read(technodata.region)
            except KeyNotFound:
                raise DependentNotFound(model, technodata.region, self._parent.region)
            regions.append(region.name)
        for comm_in in model.comm_in:
            try:
                commodity = self._parent.commodity.read(comm_in.commodity)
            except KeyNotFound:
                raise DependentNotFound(model, comm_in.commodity, self._parent.commodity)
            commodities.append(commodity.commodity)
            try:
                region = self._parent.region.read(comm_in.region)
            except KeyNotFound:
                raise DependentNotFound(model, comm_in.region, self._parent.region)
            regions.append(region.name)
        for comm_out in model.comm_out:
            try:
                commodity = self._parent.commodity.read(comm_out.commodity)
            except KeyNotFound:
                raise DependentNotFound(model, comm_out.commodity, self._parent.commodity)
            commodities.append(commodity.commodity)
            try:
                region = self._parent.region.read(comm_out.region)
            except KeyNotFound:
                raise DependentNotFound(model, comm_out.region, self._parent.region)
            regions.append(region.name)
        try:
            sector = self._parent.sector.read(model.sector)
        except KeyNotFound:
            raise DependentNotFound(model, model.sector, self._parent.sector)
        sectors.append(sector.name)
        return {
            'commodity': list(set(commodities)),
            'region': list(set(regions)),
            'sector': list(set(sectors))
        }
