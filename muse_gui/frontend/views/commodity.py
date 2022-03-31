from functools import partial
from math import inf
from typing import List

import PySimpleGUI as sg
from PySimpleGUI import Element

from muse_gui.backend.resources.datastore.exceptions import KeyAlreadyExists
from muse_gui.frontend.views.exceptions import SaveException
from muse_gui.frontend.widgets.button import SaveEditButtons

from ...backend.data.commodity import Commodity, CommodityPrice, CommodityType
from ...backend.resources.datastore import Datastore
from ..widgets.form import Form
from ..widgets.listbox import ListboxWithButtons
from ..widgets.table import FixedColumnTable
from .base import BaseView, TwoColumnMixin


def get_commodity_price(region="", time=0, value=0.0):
    return CommodityPrice(region_name=region, time=time, value=value)


def get_commodity(commodity, years=[2010], regions=["R1"], **kwargs):

    return Commodity(
        commodity=commodity,
        commodity_type=kwargs.get("commodity_type", CommodityType.energy),
        commodity_name=kwargs.get("commodity_name", ""),
        c_emission_factor_co2=kwargs.get("c_emission_factor_co2", 0.0),
        heat_rate=kwargs.get("heat_rate", 1.0),
        unit=kwargs.get("unit", "PJ"),
        price_unit=kwargs.get("price_unit", "$"),
        commodity_prices=[
            get_commodity_price(time=x, region=y) for x in years for y in regions
        ],
    )


class CommodityView(TwoColumnMixin, BaseView):
    def __init__(self, model: Datastore):
        super().__init__("commodity")
        self._parent_model = model
        self.model = model.commodity
        self._commodity_list_maker = partial(ListboxWithButtons)
        self._commodity_info_maker = partial(Form, Commodity)
        self._save_edit_btns = SaveEditButtons()

        self._prices_table_maker = partial(
            FixedColumnTable,
            1,
            3,
            2,
            pad=0,
            values=[[0, 0, 0]],
            headings=["Year", "Region", "Price"],
            expand_x=True,
            expand_y=True,
            select_mode=sg.TABLE_SELECT_MODE_NONE,
            enable_click_events=True,
        )

        self._editing = None
        self._selected = -1

    def enable_editing(self, window, force=False):
        # Careful, If enabled, form should be disabled
        # and vice versa
        if not self._editing or force:
            # Enable commodity info and table
            self._commodity_info.enable(window)
            self._prices_table.disabled = False

            # Disable list on the left
            self._commodity_list.disabled = True
            self._editing = True

    def disable_editing(self, window, force=False):
        # Careful, If disabled is true, form should be enabled
        # and vice versa
        if self._editing or force:
            # Disable commodity info and table
            self._commodity_info.disable(window)
            self._prices_table.disabled = True

            # Enable list
            self._commodity_list.disabled = False
            self._editing = False

    @property
    def selected(self):
        return self._selected

    @selected.setter
    def selected(self, v):
        self._selected = v if v is not None else -1

        if self._selected != -1 and not self.column_2.visible:
            self.column_2.update(visible=True)
            self.column_2.expand(expand_x=True, expand_y=True)

        elif self._selected == -1 and self.column_2.visible:
            self.column_2.update(visible=False)

    def _update_list(self, _commodities):
        self._commodity_list.values = _commodities

        # Update selected index, so that it doesn't fall out of the list
        self.selected = min(self.selected, len(_commodities) - 1)
        self._commodity_list.indices = [self.selected] if self.selected != -1 else None

    def _update_info(self, window, model: Commodity):
        # get prices
        _prices = model.commodity_prices
        _values = sorted(
            [[p.time, p.region_name, p.value] for p in _prices], key=lambda x: x[0]
        )

        # Set the UI view
        self._commodity_info.update(window, model)
        self._prices_table.values = _values

    def update(self, window):
        # Ensure disabled flag and elements are in sync
        if self._editing == None:
            # First time
            self.disable_editing(window, force=True)

        # Update list
        _commodity_ids = self.model.list()
        _commodities = [self.model.read(x).commodity for x in _commodity_ids]
        self._update_list(_commodities)

        if self.selected != -1:
            _commodity_info = self.model.read(_commodity_ids[self.selected])
            self._update_info(window, _commodity_info)

    def layout(self, prefix) -> List[List[Element]]:
        if not self._layout:
            self.prefix = prefix

            self._commodity_list = self._commodity_list_maker()
            self._commodity_info = self._commodity_info_maker()

            # Left Column
            self.column_1 = sg.Col(
                self._commodity_list.layout(self._prefixf()), expand_y=True
            )

            _button_layout = self._save_edit_btns.layout(self._prefixf())

            _commodity_info_layout = self._commodity_info.layout(
                self._prefixf(),
                [
                    ["commodity"],
                    ["commodity_type"],
                    ["commodity_name"],
                    ["c_emission_factor_co2"],
                    ["heat_rate"],
                    ["unit"],
                    ["price_unit"],
                ],
            )
            self._prices_table = self._prices_table_maker()
            _prices_layout = [
                [],
                [
                    sg.Text("Price Projection", auto_size_text=True),
                    sg.HorizontalSeparator(),
                ],
                [sg.Button("Add Year"), sg.Button("Zero All")],
            ] + self._prices_table.layout(self._prefixf("prices"))

            self.column_2 = sg.Column(
                _button_layout
                + [[sg.HorizontalSeparator()]]
                + _commodity_info_layout
                + _prices_layout,
                expand_x=True,
                expand_y=True,
            )

            self._layout = [
                [self.column_1, self.column_2],
            ]
        return self._layout

    def bind_handlers(self):
        self._prices_table.bind_handlers()

    def _handle_edit(self, window):
        if self._editing == True:
            # Already in edit state, so reset
            # Disable save, enable edit
            self._save_edit_btns.state = "idle"
            self.disable_editing(window)

            self.update(window)
            return "idle", self.key

        # Disable edit, enable save
        self._save_edit_btns.state = "edit"

        # Enable sector info, disable list
        self.enable_editing(window)

        # Communicate edit mode to parent
        return "edit", self.key

    def _handle_save(self, window, values):
        # Commit to datastore

        # Get current values from view
        _values = self._commodity_info.read(values)
        _values["commodity_prices"] = [
            {
                "time": x[0],
                "region_name": x[1],
                "value": x[2],
            }
            for x in self._prices_table.values
        ]

        # Get name in the form
        new_name = _values["commodity"]

        # Check if it is add mode / edit mode
        _ids = self.model.list()

        if self.selected == len(_ids):
            # Add mode
            try:
                commodity = Commodity.parse_obj(_values)
                self.model.create(commodity)
            except KeyAlreadyExists:
                raise SaveException(f'Commodity with name "{new_name}" already exists!')
            except Exception as e:
                raise SaveException() from e
        else:
            # Update mode
            # Get current model key
            _commodity_id = _ids[self.selected]
            _commodity = self.model.read(_commodity_id)

            if new_name != _commodity.commodity:
                deps = self.model.forward_dependents(_commodity)
                for d in deps:
                    if len(deps[d]):
                        # Not supporting name change for ones with forward deps
                        raise SaveException() from RuntimeError(
                            "Changing name is not supported for commodities already associated with resources"
                        )

            _model_dict = _commodity.dict()
            _model_dict.update(_values)
            try:
                commodity = Commodity.parse_obj(_model_dict)
                self.model.update(_commodity_id, commodity)
                # Fingers crossed
            except Exception as e:
                raise SaveException() from e

        # Disable save, enable edit
        self._save_edit_btns.state = "idle"
        self.disable_editing(window)

        self.update(window)
        # Communicate save mode to parent
        return "idle", self.key

    def _handle_add_commodity(self, window):
        # Create a standard sector
        commodity = sg.popup_get_text(
            "Please enter name of commodity to add",
            "Add Commodity",
            "New Commodity",
        )
        if commodity == None or commodity.strip() == "":
            return None, "0 commodities added"

        # Create a dummy commodity with given name
        available_years = [
            self._parent_model.available_year.read(x).year
            for x in self._parent_model.available_year.list()
        ]
        available_regions = [
            self._parent_model.region.read(x).name
            for x in self._parent_model.region.list()
        ]
        # and update view
        commodity = commodity.strip()
        _commodity = get_commodity(
            commodity,
            years=available_years,
            regions=available_regions,
        )

        _commodity_ids = self.model.list()
        _commodities = [self.model.read(x).commodity for x in _commodity_ids]

        _commodities.append(commodity)
        self.selected = inf
        self._update_list(_commodities)
        self._update_info(window, _commodity)

        # Simulate edit mode
        return self._handle_edit(window)

    def _handle_delete_commodity_safe(self, id):
        """
        Internal function that deletes the commodity
        returns True / False based on whether commodity was deleted or not
        """
        _commodity = self.model.read(id)
        # Compute forward dependencies
        deps = self.model.forward_dependents_recursive(_commodity)

        # Check if deps are empty
        empty_deps = True
        dep_string = ""
        for d in deps:
            if len(deps[d]):
                empty_deps = False
                dep_string += f"{d}:\n"
                dep_string += ",".join(deps[d])
                dep_string += "\n\n"

        # Show popup to confirm
        if not empty_deps:
            ret = sg.popup_yes_no(
                f"Deleting commodity {_commodity.commodity} will result in the following being deleted:\n",
                f"{dep_string}" f"Delete anyway?\n",
                title="Warning!",
            )
            if ret and ret == "Yes":
                self.model.delete(id)
                return True
            else:
                return False
        else:
            self.model.delete(id)
            return True

    def _handle_delete_commodity(self, window):
        if self.selected == -1:
            return None, "Select a commodity before attempting to delete!"

        selected_commodity = self.model.list()[self.selected]

        is_deleted = self._handle_delete_commodity_safe(selected_commodity)
        if not is_deleted:
            return
        self._selected = max(0, self._selected - 1)
        self.update(window)
        return None, f'Commodity "{selected_commodity}" deleted'

    def __call__(self, window, event, values):
        print("Commodity view handling - ", event)
        address = event
        if event[0] and isinstance(event[0], tuple):
            address = event[0]

        _event = address[len(self._prefixf()) :][0]

        if _event == "listbox":
            # Selection event
            indices = self._commodity_list.indices
            if len(indices):
                self.selected = indices[-1]
                self.update(window)

        elif _event == "prices":
            self._prices_table(window, event, values)

        elif _event == "add":
            # Add Commodity
            return self._handle_add_commodity(window)

        elif _event == "delete":
            # Delete sector
            return self._handle_delete_commodity(window)

        elif _event == "edit":
            # Edit event
            return self._handle_edit(window)

        elif _event == "save":
            # Save event - Commit to datastore / throw
            return self._handle_save(window, values)
        else:
            print("Unhandled event - ", event)

        return None
