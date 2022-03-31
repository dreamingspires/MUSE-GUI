from typing import TYPE_CHECKING, Dict, List

from muse_gui.backend.data.timeslice import AvailableYear
from muse_gui.backend.resources.datastore.base import BaseDatastore
from muse_gui.backend.resources.datastore.exceptions import KeyNotFound

if TYPE_CHECKING:
    from . import Datastore


class AvailableYearDatastore(BaseDatastore[AvailableYear]):
    def __init__(
        self, parent: "Datastore", available_years: List[AvailableYear] = []
    ) -> None:
        super().__init__(parent, "year", data=available_years)

    def forward_dependents(self, model: AvailableYear) -> Dict[str, List[str]]:
        commodities = []
        for key, commodity in self._parent.commodity._data.items():
            for price in commodity.commodity_prices:
                if price.time == model.year:
                    commodities.append(key)
        return {"commodity": list(set(commodities))}
