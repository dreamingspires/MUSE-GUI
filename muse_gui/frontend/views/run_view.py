from functools import partial
from typing import Any, Dict, List, Optional

import PySimpleGUI as sg
from PySimpleGUI import Element

from muse_gui.backend.data.run_model import CarbonMarket, MethodOptions, RunModel
from muse_gui.backend.resources.datastore import Datastore
from muse_gui.frontend.popups.associations_popup import show_dual_listbox
from muse_gui.frontend.views.base import BaseView
from muse_gui.frontend.views.exceptions import SaveException
from muse_gui.frontend.widgets.base import BaseWidget
from muse_gui.frontend.widgets.form import Form
from muse_gui.frontend.widgets.table import FixedColumnTable


class CarbonMarketInfo(BaseWidget):
    def __init__(self, key: Optional[str] = None):
        super().__init__(key)

        self._activate_maker = partial(
            sg.Checkbox, "Activate Carbon Market", enable_events=True
        )
        self._method_options_maker = partial(
            sg.OptionMenu,
            [None] + [x.value for x in MethodOptions],
            default_value=None,
        )
        self._budget_table = FixedColumnTable(
            0,
            2,
            1,
            num_rows=10,
            pad=0,
            values=[[]],
            headings=["Year", "Budget"],
            expand_x=True,
            select_mode=sg.TABLE_SELECT_MODE_NONE,
            enable_click_events=True,
        )

    def _set_textbox_with_list(self, window, key: str, val: List):
        _text = ", ".join(val)
        window[self._prefixf(key)](_text)

    def set_commodities(self, window, val):
        self._set_textbox_with_list(window, "commodities", val)

    def update(self, window, model: CarbonMarket):
        # Update commodities
        _comm = [] if model.commodities == None else model.commodities
        self.set_commodities(window, _comm)

        # Update options
        window[self._prefixf("undershoot")].update(value=model.control_undershoot)
        window[self._prefixf("overshoot")].update(value=model.control_overshoot)
        self._method_options.update(value=model.method_options)

    # Activate or deactivate carbonmarket
    def activate(self, window):
        self._budget_table.disabled = False
        window[self._prefixf("frame")].update(visible=True)

    def deactivate(self, window):
        self._budget_table.disabled = True
        window[self._prefixf("frame")].update(visible=False)

    def get_budget(self):
        return self._budget_table.values

    def set_budget(self, values):
        self._budget_table.values = values

    def read(self, values) -> Dict[str, Any]:
        return {
            "budget": self._budget_table.values,
            "control_undershoot": values[self._prefixf("undershoot")],
            "control_overshoot": values[self._prefixf("overshoot")],
            "method_options": values[self._prefixf("method_options")],
        }

    def layout(self, prefix) -> List[List[Element]]:
        if not self._layout:
            self.prefix = prefix
            self._activate = self._activate_maker(
                key=self._prefixf("activate_carbon_market")
            )
            self._method_options = self._method_options_maker(
                key=self._prefixf("method_options")
            )

            _commodities = sg.Frame(
                "Commodities",
                [
                    [
                        sg.Multiline(
                            "",
                            size=(20, 2),
                            disabled=True,
                            expand_x=True,
                            write_only=True,
                            key=self._prefixf("commodities"),
                        ),
                        sg.Button("Change", key=self._prefixf("edit_commodities")),
                    ]
                ],
                element_justification="center",
                expand_x=True,
            )

            self._layout = [
                [self._activate],
                [
                    sg.Frame(
                        "Carbon Market",
                        key=self._prefixf("frame"),
                        visible=False,
                        expand_x=True,
                        layout=self._budget_table.layout(self._prefixf("budget"))
                        + [
                            [_commodities],
                            [
                                sg.Checkbox(
                                    "Control undershoot",
                                    key=self._prefixf("undershoot"),
                                )
                            ],
                            [
                                sg.Checkbox(
                                    "Control overshoot", key=self._prefixf("overshoot")
                                )
                            ],
                            [
                                sg.Text("Fit Method: ", auto_size_text=True),
                                self._method_options,
                            ],
                        ],
                    )
                ],
            ]
        return self._layout

    def bind_handlers(self):
        self._budget_table.bind_handlers()


class SettingsInfo(BaseWidget):
    def __init__(self, key: Optional[str] = None):
        super().__init__(key)

        self._info = Form(RunModel)

    def update(self, window, model: RunModel):

        # Update form
        self._info.update(window, model)

        # Update regions, time_framework, Excluded
        _regions = sorted(model.regions)
        self.set_regions(window, _regions)

        _timeframework = sorted(model.time_framework)
        self.set_timeframework(window, _timeframework)

        _excluded_comms = model.excluded_commodities
        self.set_excluded_commodities(window, _excluded_comms)

        # update interest rate
        window[self._prefixf("interest_rate")].update(value=model.interest_rate)

    def read(self, values) -> Dict[str, Any]:
        _values = self._info.read(values)
        _values.update(
            {
                "interest_rate": values[self._prefixf("interest_rate")],
            }
        )

        return _values

    def _set_textbox_with_list(self, window, key: str, val: List):
        _text = ", ".join([str(x) for x in val])
        window[self._prefixf(key)](_text)

    def set_regions(self, window, val):
        self._set_textbox_with_list(window, "regions", val)

    def set_timeframework(self, window, val):
        self._set_textbox_with_list(window, "timeframework", val)

    def set_excluded_commodities(self, window, val):
        self._set_textbox_with_list(window, "excluded_commodities", val)

    def layout(self, prefix):
        if not self._layout:
            self.prefix = prefix

            _regions = sg.Frame(
                "Selected Regions",
                [
                    [
                        sg.Multiline(
                            "",
                            size=(20, 2),
                            disabled=True,
                            expand_x=True,
                            write_only=True,
                            key=self._prefixf("regions"),
                        ),
                        sg.Button("Change", key=self._prefixf("edit_regions")),
                    ]
                ],
                expand_x=True,
                element_justification="center",
            )

            _timeframework = sg.Frame(
                "Time Framework",
                [
                    [
                        sg.Multiline(
                            "",
                            size=(20, 2),
                            disabled=True,
                            expand_x=True,
                            write_only=True,
                            key=self._prefixf("timeframework"),
                        ),
                        sg.Button("Change", key=self._prefixf("edit_timeframework")),
                    ]
                ],
                expand_x=True,
                element_justification="center",
            )

            _form_layout = self._info.layout(
                self._prefixf(),
                [
                    ["interpolation_mode"],
                    ["equilibrium_variable"],
                    ["maximum_iterations"],
                    ["tolerance"],
                    ["tolerance_unmet_demand"],
                    ["foresight"],
                    ["log_level"],
                ],
            )

            self._layout = [
                [_regions],
                [_timeframework],
                [sg.Text("")],
                [
                    sg.Text("Excluded Commodities", size=(20, 1)),
                    sg.Text(":", auto_size_text=True),
                    sg.Multiline(
                        "",
                        size=(20, 2),
                        expand_x=True,
                        write_only=True,
                        key=self._prefixf("excluded_commodities"),
                    ),
                ],
                [
                    sg.Text("Interest Rate", size=(20, 1)),
                    sg.Text(":", auto_size_text=True),
                    sg.Input(
                        "",
                        size=(8, 1),
                        justification="right",
                        key=self._prefixf("interest_rate"),
                    ),
                ],
            ] + _form_layout

        return self._layout


class RunView(BaseView):
    def __init__(self, model: Datastore):
        super().__init__("run")
        self._datastore = model
        self.model = model.run_settings or RunModel(
            regions=self._datastore.region.list(),
            time_framework=[int(x) for x in self._datastore.available_year.list()],
            interest_rate=None,
        )
        self.carbon_model = self.model.carbon_budget_control or CarbonMarket()

        self._carbon_market = CarbonMarketInfo()
        self._info = SettingsInfo()

        self._regions = []
        self._timeframework = []
        self._carbon_market_commodities = []

        self._updated = False

    def layout(self, prefix):
        if not self._layout:
            self.prefix = prefix
            self._layout = [
                [
                    sg.Column(
                        self._info.layout(self._prefixf()),
                        expand_x=True,
                        expand_y=True,
                    ),
                    sg.Column(
                        self._carbon_market.layout(self._prefixf()),
                        expand_x=True,
                        expand_y=True,
                    ),
                ],
                [
                    sg.Text(""),
                ],
                [
                    sg.Push(),
                    sg.Button("Run Muse", key=self._prefixf("run"), size=(20, 2)),
                    sg.Push(),
                ],
            ]

        return self._layout

    def bind_handlers(self):
        self._carbon_market.bind_handlers()

    def _patch_budget(self):
        # Patch budget table
        _budget_values = self._carbon_market.get_budget()

        _budget_map = {int(x[0]): x[1] for x in _budget_values if x}

        _new_budget = [
            [x, _budget_map[x]] if x in _budget_map else [x, ""]
            for x in self._timeframework
        ]

        self._carbon_market.set_budget(_new_budget)

    def update(self, window):

        if self._updated == False:
            # Tab is loading for the first time
            self._timeframework = sorted(self.model.time_framework)
            self._regions = sorted(self.model.regions)
            self._carbon_market_commodities = self.carbon_model.commodities or []
            self._carbon_market.update(window, self.carbon_model)
            self._info.update(window, self.model)
            self._updated = True

        # Update regions
        available_regions = self._datastore.region.list()
        self._regions = [x for x in self._regions if x in available_regions]
        self._info.set_regions(window, self._regions)

        # Update timeframework
        available_years = [
            self._datastore.available_year.read(x).year
            for x in self._datastore.available_year.list()
        ]
        self._timeframework = [x for x in self._timeframework if x in available_years]
        self._info.set_timeframework(window, self._timeframework)

        self._patch_budget()

        # Update carbon market commodities
        available_commodities = self._datastore.commodity.list()
        self._carbon_market_commodities = [
            x for x in self._carbon_market_commodities if x in available_commodities
        ]
        self._carbon_market.set_commodities(window, self._carbon_market_commodities)

    def __call__(self, window, event, values):
        print("Run view handling - ", event)
        address = event
        if event[0] and isinstance(event[0], tuple):
            address = event[0]

        _event = address[len(self._prefixf()) :][0]

        if _event == "activate_carbon_market":
            # Check state and activate / deactivate
            _state = values[self._prefixf("activate_carbon_market")]
            if _state:
                self._carbon_market.activate(window)
            else:
                self._carbon_market.deactivate(window)
        elif _event == "edit_regions":
            return self._handle_edit_regions(window)
        elif _event == "edit_timeframework":
            return self._handle_edit_years(window)
        elif _event == "edit_commodities":
            return self._handle_edit_commodities(window)
        elif _event == "run":
            return self._handle_run(window, values)
        elif (
            _event == "budget"
            or self._carbon_market._budget_table.should_handle_event(event)
        ):
            return self._carbon_market._budget_table(window, event, values)
        else:
            super().__call__(window, event, values)

    def _handle_run(self, window, values):
        # Read all UI Values and create a model
        _values = self._info.read(values)
        _values["regions"] = self._regions
        _values["time_framework"] = self._timeframework
        _values["carbon_budget_control"] = None
        _values["excluded_commodities"] = [
            x.strip()
            for x in window[self._prefixf("excluded_commodities")].get().split(",")
            if x.strip()
        ]
        # Is carbon market active?
        _state = values[self._prefixf("activate_carbon_market")]
        if _state:
            # Read UI values
            _cm_values = self._carbon_market.read(values)

            # Map budget back from table to list
            _budget = [x[1] for x in _cm_values["budget"] if x and x[1]]
            _cm_values.pop("budget")
            if len(_budget) != len(self._timeframework):
                raise SaveException("Carbon market Budget not specified for all years!")

            _values["carbon_budget_control"] = CarbonMarket(
                **_cm_values,
                budget=_budget,
                commodities=self._carbon_market_commodities
                if self._carbon_market_commodities
                else None
            )

        current_model_dict = self.model.dict()
        current_model_dict.update(_values)
        self._datastore.run_settings = RunModel.parse_obj(current_model_dict)

    def _handle_edit_commodities(self, window):
        current_comm = self._carbon_market_commodities[:]

        all_commodities = self._datastore.commodity.list()

        _, self._carbon_market_commodities = show_dual_listbox(
            "Carbon Market Commodities",
            v_one=[x for x in all_commodities if x not in current_comm],
            v_two=self._carbon_market_commodities,
        )

        self._carbon_market.set_commodities(window, self._carbon_market_commodities)

    def _handle_edit_regions(self, window):
        current_regions = self._regions[:]
        all_regions = self._datastore.region.list()
        _, self._regions = show_dual_listbox(
            "Regions",
            v_one=[x for x in all_regions if x not in current_regions],
            v_two=self._regions,
        )
        self._regions = sorted(self._regions)
        self._info.set_regions(window, self._regions)

    def _handle_edit_years(self, window):
        current_years = self._timeframework[:]
        all_years = self._datastore.available_year.list()

        _, self._timeframework = show_dual_listbox(
            "Time Framework",
            v_one=[x for x in all_years if int(x) not in current_years],
            v_two=self._timeframework,
        )

        self._timeframework = sorted([int(x) for x in self._timeframework])

        self._info.set_timeframework(window, self._timeframework)
        # Patch budget
        self._patch_budget()
