from typing import TYPE_CHECKING, Dict, List

from muse_gui.backend.data.process import Process
from muse_gui.backend.resources.datastore.base import BaseDatastore
from muse_gui.backend.resources.datastore.exceptions import (
    DependentNotFound,
    KeyNotFound,
)

if TYPE_CHECKING:
    from . import Datastore


class ProcessDatastore(BaseDatastore[Process]):
    def __init__(self, parent: "Datastore", level_names: List[Process] = []) -> None:
        super().__init__(parent, "name", data=level_names)

    def back_dependents(self, model: Process) -> Dict[str, List[str]]:
        commodities: List[str] = []
        regions: List[str] = []
        sectors: List[str] = []
        agents: List[str] = []
        for technodata in model.technodatas:
            try:
                region = self._parent.region.read(technodata.region)
            except KeyNotFound:
                raise DependentNotFound(model, technodata.region, self._parent.region)
            regions.append(region.name)
            for agent in technodata.agents:
                try:
                    self._parent.agent.read(agent.agent_name)
                except KeyNotFound:
                    raise DependentNotFound(model, agent.agent_name, self._parent.agent)
                agents.append(agent.agent_name)
        for comm_in in model.comm_in:
            try:
                commodity = self._parent.commodity.read(comm_in.commodity)
            except KeyNotFound:
                raise DependentNotFound(
                    model, comm_in.commodity, self._parent.commodity
                )
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
                raise DependentNotFound(
                    model, comm_out.commodity, self._parent.commodity
                )
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
        try:
            if model.preset_sector is not None:
                sector = self._parent.sector.read(model.preset_sector)
                sectors.append(sector.name)
        except KeyNotFound:
            raise DependentNotFound(model, model.preset_sector, self._parent.sector)

        return {
            "commodity": list(set(commodities)),
            "region": list(set(regions)),
            "sector": list(set(sectors)),
            "agent": list(set(agents)),
        }
