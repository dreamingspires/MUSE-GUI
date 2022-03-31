import textwrap
from functools import partial
from math import inf
from typing import Any, Dict, List, Literal, Optional, Tuple

import PySimpleGUI as sg
from pydantic import root_validator
from PySimpleGUI import Element

from muse_gui.backend.data.agent import AgentType
from muse_gui.backend.data.sector import SectorType
from muse_gui.backend.resources.datastore.exceptions import KeyAlreadyExists
from muse_gui.frontend.popups import show_dual_listbox
from muse_gui.frontend.views.exceptions import SaveException
from muse_gui.frontend.widgets.base import BaseWidget
from muse_gui.frontend.widgets.button import SaveEditButtons
from muse_gui.frontend.widgets.utils import render

from ...backend.data.process import (
    Capacity,
    CapacityShare,
    CommodityFlow,
    Cost,
    ExistingCapacity,
    Process,
    Technodata,
    Utilisation,
)
from ...backend.resources.datastore import Datastore
from ..widgets.form import Form
from ..widgets.listbox import ListboxWithButtons
from ..widgets.table import FixedColumnTable
from .base import BaseView, TwoColumnMixin

FIXED_TABLES = {
    "capacity": [
        "Max Addition",
        "Max Growth",
        "Total Limit",
        "Technical Life",
        "Scaling Size",
        "Utilisation Factor",
        "Efficiency",
    ],
    "cost": [
        "cap_par",
        "cap_exp",
        "fix_par",
        "fix_exp",
        "var_par",
        "var_exp",
        "Interest Rate",
    ],
    "existing_capacity": ["Qty"],
}


class DummyProcess(Process):
    @root_validator
    def at_least_one_in_or_out(cls, values):
        # Override
        return values


class TechnologyModelHelper:
    def __init__(self, model: Datastore):
        self._process = model.process
        self._agent = model.agent
        self._sector = model.sector
        self._commodity = model.commodity
        self._region = model.region
        self._available_years = model.available_year

    @property
    def regions(self):
        return self._region.list()

    @property
    def sectors(self):
        return self._sector.list()

    @property
    def agents(self):
        return self._agent.list()

    @property
    def available_years(self):
        return [
            self._available_years.read(x).year for x in self._available_years.list()
        ]

    @property
    def standard_sectors(self):
        return [
            x for x in self.sectors if self._sector.read(x).type == SectorType.STANDARD
        ]

    @property
    def preset_sectors(self):
        return [
            x for x in self.sectors if self._sector.read(x).type == SectorType.PRESET
        ]

    def get_agent_share_map_for_regions(
        self, _regions: List[str]
    ) -> Dict[Tuple[str, AgentType, str], str]:
        if len(_regions) == 0:
            return {}

        share_names = {}
        for x in self.agents:
            _agent = self._agent.read(x)
            # TODO Change to itertools chain?
            share_names.update(
                {
                    (_agent.name, "Retrofit", r): _data.share
                    for r, _data in _agent.retrofit.items()
                    if r in _regions
                }
            )
            share_names.update(
                {
                    (_agent.name, "New", r): _data.share
                    for r, _data in _agent.new.items()
                    if r in _regions
                }
            )

        return share_names

    @property
    def commodities(self):
        return self._commodity.list()

    @property
    def processes(self):
        return self._process.list()

    def get_process(self, id: str):
        return self._process.read(id)

    def get_technodata_regions_for_process(self, _process: Process):
        return sorted(list(dict.fromkeys(x.region for x in _process.technodatas)))

    def get_technodata_years_for_process(self, _process: Process):
        return sorted(list(dict.fromkeys(int(x.time) for x in _process.technodatas)))

    def get_inputs_for_process(self, _process: Process):
        return sorted(list(dict.fromkeys(x.commodity for x in _process.comm_in)))

    def get_outputs_for_process(self, _process: Process):
        return sorted(list(dict.fromkeys(x.commodity for x in _process.comm_out)))

    def get_additional_inputs_for_process(self, _process: Process):
        return sorted(
            list(
                dict.fromkeys(
                    x.commodity
                    for x in _process.comm_in
                    if x.commodity.lower() != _process.fuel.lower()
                )
            )
        )

    def get_additional_outputs_for_process(self, _process: Process):
        return sorted(
            list(
                dict.fromkeys(
                    x.commodity
                    for x in _process.comm_out
                    if x.commodity.lower() != _process.end_use.lower()
                )
            )
        )

    def get_existing_capacity_for_process(
        self, process: Process, rows: List[Tuple[int, str]]
    ):
        if len(rows) == 0:
            return [[]]
        _values: Dict[Tuple[int, str], List[float]] = {}
        for x in process.existing_capacities:
            _val = [x.value]
            _key = (int(x.year), x.region)
            _values[_key] = _val

        sort_keys = sorted(rows)
        return [list(k) + (_values[k] if k in _values else [""]) for k in sort_keys]

    def get_capacity_for_process(self, _process: Process, rows: List[Tuple[int, str]]):
        if len(rows) == 0:
            return [[]]
        _values = {}
        NCOLS = 7
        for x in _process.technodatas:
            _val = [
                x.capacity.max_capacity_addition,
                x.capacity.max_capacity_growth,
                x.capacity.total_capacity_limit,
                x.capacity.technical_life,
                x.capacity.scaling_size,
                x.utilisation.utilization_factor,
                x.utilisation.efficiency,
            ]
            _key = (int(x.time), x.region)
            _values[_key] = _val

        sort_keys = sorted(rows)
        return [
            list(k) + (_values[k] if k in _values else ["" for _ in range(NCOLS)])
            for k in sort_keys
        ]

    def get_cost_for_process(self, _process: Process, rows: List[Tuple[int, str]]):
        if len(rows) == 0:
            return [[]]
        _values = {}
        NCOLS = 7
        for x in _process.technodatas:
            _val = [
                x.cost.cap_par,
                x.cost.cap_exp,
                x.cost.fix_par,
                x.cost.fix_exp,
                x.cost.var_par,
                x.cost.var_exp,
                x.cost.interest_rate,
            ]
            _key = (int(x.time), x.region)
            _values[_key] = _val

        sort_keys = sorted(rows)
        return [
            list(k) + (_values[k] if k in _values else ["" for _ in range(NCOLS)])
            for k in sort_keys
        ]

    def _get_comm_table_for_process(
        self,
        _process: Process,
        key: Literal["input", "output"],
        rows: List[Tuple[int, str]],
        cols: List[str],
    ) -> List[List]:

        if len(rows) == 0:
            return [[]]
        # Get current process input commodities into a map from (year, region, commodity) -> commodity qty
        _values = {}
        _attribute = None
        if key == "input":
            _attribute = _process.comm_in
        elif key == "output":
            _attribute = _process.comm_out
        else:
            raise ValueError(f'Only supported for keys ["input", "output"] - Got {key}')

        for comm in _attribute:
            _year, _region, _commodity, _value = (
                comm.timeslice,
                comm.region,
                comm.commodity,
                comm.value,
            )
            _key = (int(_year), _region)
            if _key not in _values:
                _values[_key] = {}

            _values[_key][_commodity.lower()] = _value

        sort_keys = sorted(rows)

        lower_cols = [x.lower() for x in cols]
        return [
            list(k)
            + [
                _values[k][x] if k in _values and x in _values[k] else ""
                for x in lower_cols
            ]
            for k in sort_keys
        ]

    def get_commout_table_for_process(
        self, _process: Process, rows: List[Tuple[int, str]], cols: List[str]
    ):
        return self._get_comm_table_for_process(_process, "output", rows, cols)

    def get_commin_table_for_process(
        self, _process: Process, rows: List[Tuple[int, str]], cols: List[str]
    ):
        return self._get_comm_table_for_process(_process, "input", rows, cols)

    def get_agent_table_for_process(
        self,
        _process: Process,
        rows: List[Tuple[int, str]],
        cols: Dict[Tuple[str, AgentType, str], str],
    ):
        if len(rows) == 0:
            return [[]]
        # Update agents
        # Get current process agent shares into a map from (year, region, agent) -> share
        _values = {}
        for tdata in _process.technodatas:
            _year, _region, _agents = tdata.time, tdata.region, tdata.agents
            _key = (int(_year), _region)
            if _key not in _values:
                _values[_key] = {}

            for _agent in _agents:
                _agent_key = (_agent.agent_name, _agent.agent_type, _agent.region)
                _values[_key][_agent_key] = _agent.share

        sort_keys = sorted(rows)

        return [
            list(k)
            + [_values[k][x] if k in _values and x in _values[k] else 0 for x in cols]
            for k in sort_keys
        ]


class TechnologyInfo(BaseWidget):
    def __init__(self, key: Optional[str] = None):
        super().__init__(key)

        # Tech info
        self._tech_info = Form(Process)
        option_menu_f_maker = partial(sg.OptionMenu, [None])

        self._render_fields = {
            "sector": option_menu_f_maker,
            "fuel": option_menu_f_maker,
            "end_use": option_menu_f_maker,
            "preset_sector": option_menu_f_maker,
        }
        self._editing = None

    def read(self, values):
        _form_values = self._tech_info.read(values)
        _form_values.update(
            {
                "sector": values[self._prefixf("sector")],
                "fuel": values[self._prefixf("fuel")],
                "end_use": values[self._prefixf("end_use")],
                "preset_sector": values[self._prefixf("preset_sector")],
            }
        )
        return _form_values

    def enable_editing(self, window, force=False):
        if not self._editing or force:
            # Enable form fields
            self._tech_info.enable(window)

            window[self._prefixf("sector")](disabled=False)
            window[self._prefixf("fuel")](disabled=False)
            window[self._prefixf("end_use")](disabled=False)
            window[self._prefixf("preset_sector")](disabled=False)

            # Enable association buttons
            window[self._prefixf("edit_regions")](disabled=False)
            window[self._prefixf("edit_inputs")](disabled=False)
            window[self._prefixf("edit_outputs")](disabled=False)

            self._editing = True

    def disable_editing(self, window, force=False):
        if self._editing or force:
            # Enable form fields
            self._tech_info.disable(window)

            window[self._prefixf("sector")](disabled=True)
            window[self._prefixf("fuel")](disabled=True)
            window[self._prefixf("end_use")](disabled=True)
            window[self._prefixf("preset_sector")](disabled=True)

            # Enable association buttons
            window[self._prefixf("edit_regions")](disabled=True)
            window[self._prefixf("edit_inputs")](disabled=True)
            window[self._prefixf("edit_outputs")](disabled=True)

            self._editing = False

    def _set_textbox_with_list(self, window, key: str, val: List):
        _text = ",".join(val)
        _text = textwrap.fill(_text, 20, max_lines=2, placeholder="...")
        window[self._prefixf(key)](_text)

    def set_regions(self, window, val):
        self._set_textbox_with_list(window, "regions", val)

    def set_inputs(self, window, val):
        self._set_textbox_with_list(window, "commin", val)

    def set_outputs(self, window, val):
        self._set_textbox_with_list(window, "commout", val)

    def set_sector_options(self, window, val):
        window[self._prefixf("sector")](values=val)

    def set_preset_options(self, window, val):
        window[self._prefixf("preset_sector")](values=val)

    def set_commodity_options(self, window, val):
        window[self._prefixf("fuel")](values=val)
        window[self._prefixf("end_use")](values=val)

    def bind_handlers(self):
        pass

    def update(self, window, process: Process):

        # Update form
        self._tech_info.update(window, process)

        _fuel = process.fuel
        _end_use = process.end_use
        # Update sectors, fuel, enduse
        window[self._prefixf("sector")].update(value=process.sector)
        window[self._prefixf("fuel")].update(value=_fuel)
        window[self._prefixf("end_use")].update(value=_end_use)
        window[self._prefixf("preset_sector")].update(value=process.preset_sector)

        # Update commin commout
        _regions = sorted(list(dict.fromkeys(x.region for x in process.technodatas)))
        self.set_regions(window, _regions)

        # TODO Why is the string in fuel and commodity are different?
        _inputs = sorted(
            list(
                dict.fromkeys(
                    x.commodity
                    for x in process.comm_in
                    if x.commodity.lower() != _fuel.lower()
                )
            )
        )
        self.set_inputs(window, _inputs)

        _outputs = sorted(
            list(
                dict.fromkeys(
                    x.commodity
                    for x in process.comm_out
                    if x.commodity.lower() != _end_use.lower()
                )
            )
        )
        self.set_outputs(window, _outputs)

    def layout(self, prefix):
        if not self._layout:
            self.prefix = prefix

            # Layout form
            _tech_info_layout = self._tech_info.layout(
                self._prefixf(),
                [
                    ["name"],
                    ["type"],
                ],
            )

            # Layout option menu
            _tech_options_layout = render(self._render_fields, _prefix=self._prefixf())

            _column1 = sg.Column(
                _tech_info_layout + _tech_options_layout, expand_y=True
            )
            # Layout associations
            _tech_associations_layout = [
                [
                    sg.Frame(
                        "Addn. Inputs",
                        [
                            [
                                sg.Multiline(
                                    "",
                                    size=(20, 2),
                                    disabled=True,
                                    write_only=True,
                                    no_scrollbar=True,
                                    key=self._prefixf("commin"),
                                ),
                                sg.Button("Change", key=self._prefixf("edit_inputs")),
                            ]
                        ],
                        element_justification="center",
                    ),
                ],
                [
                    sg.Frame(
                        "Addn. Outputs",
                        [
                            [
                                sg.Multiline(
                                    "",
                                    size=(20, 2),
                                    disabled=True,
                                    write_only=True,
                                    no_scrollbar=True,
                                    key=self._prefixf("commout"),
                                ),
                                sg.Button("Change", key=self._prefixf("edit_outputs")),
                            ]
                        ],
                        element_justification="center",
                    ),
                ],
                [
                    sg.Frame(
                        "Regions",
                        [
                            [
                                sg.Multiline(
                                    "",
                                    size=(20, 2),
                                    disabled=True,
                                    write_only=True,
                                    no_scrollbar=True,
                                    key=self._prefixf("regions"),
                                ),
                                sg.Button("Change", key=self._prefixf("edit_regions")),
                            ]
                        ],
                        element_justification="center",
                    ),
                ],
            ]
            _column2 = sg.Column(_tech_associations_layout, expand_y=True)

            self._layout = [
                [_column1, _column2],
            ]

        return self._layout


class TechnologyTables(BaseWidget):
    def __init__(self, tab_headings: List[str], key: Optional[str] = None):
        super().__init__(key)
        self._tab_headings = tab_headings
        self._tables = self._create_tables()
        self._disabled = False

    def disable_tabs(self, window):
        current_tab = self._tabgroup.get()
        for k in self._tab_headings:
            _tabkey = self._tabgroup.find_key_from_tab_name(k.replace("_", " ").title())
            if _tabkey and _tabkey != current_tab:
                window[_tabkey](disabled=True)

    def enable_tabs(self, window):
        for k in self._tab_headings:
            _tabkey = self._tabgroup.find_key_from_tab_name(k.replace("_", " ").title())
            if _tabkey:
                window[_tabkey](disabled=False)

    @property
    def disabled(self):
        return self._disabled

    @disabled.setter
    def disabled(self, val):
        for k in self._tables:
            self._tables[k].disabled = val
        self._disabled = val

    def bind_handlers(self):
        for k in self._tables:
            self._tables[k].bind_handlers()

    def update(self, values: Dict[str, List[List]]):
        for k in self._tables:
            if k in values:
                self._tables[k].values = values[k]

    def layout(self, prefix):
        if not self._layout:
            self.prefix = prefix

            _tech_table_layout = []
            for k in self._tab_headings:
                if k in FIXED_TABLES:
                    _table_layout = self._tables[k].layout(self._prefixf(k))
                else:
                    _table_layout = [
                        [
                            sg.Frame(
                                "",
                                [
                                    [
                                        sg.Text(
                                            "Table opened in  new window. Close to proceed"
                                        )
                                    ]
                                ],
                                expand_x=True,
                                expand_y=True,
                                vertical_alignment="center",
                                element_justification="center",
                            )
                        ]
                    ]

                _tech_table_layout.append(
                    [sg.Tab(k.replace("_", " ").title(), _table_layout)]
                )

            self._tabgroup = sg.TabGroup(
                _tech_table_layout,
                expand_x=True,
                expand_y=True,
                enable_events=True,
                key=self._prefixf("tabs"),
            )
            self._layout = [[self._tabgroup]]
        return self._layout

    def __call__(self, window, event, values):
        print("Technology tables view handling - ", event)
        address = event
        if event[0] and isinstance(event[0], tuple):
            address = event[0]

        _event = address[len(self._prefixf()) :][0]

        if _event in FIXED_TABLES:
            self._tables[_event](window, event, values)
            return None

        if _event == "tabs":
            # Tab switch event
            return values[self._prefixf("tabs")].lower().replace(" ", "_")

    def _get_table(self, headings: List[str], values=[[]]) -> FixedColumnTable:
        _headings = ["Year", "Region"] + headings
        return FixedColumnTable(
            0,
            len(_headings),
            2,
            pad=0,
            values=values,
            headings=_headings,
            expand_x=True,
            expand_y=True,
            select_mode=sg.TABLE_SELECT_MODE_NONE,
            enable_click_events=True,
        )

    def _create_tables(self) -> Dict[str, FixedColumnTable]:
        return {k: self._get_table(FIXED_TABLES[k]) for k in FIXED_TABLES}

    def read(self, key: str):
        return self._tables[key].values

    def show_table(
        self, key: str, values: List[List], headings=None, disabled=True
    ) -> Optional[List[List]]:
        if key in self._tables:
            self._tables[key].values = values
            self._tables[key].disabled = disabled
            return None

        if headings is None:
            raise ValueError("Headings must be provided")

        return self._show_table(key, headings, values, disabled)

    def _show_table(
        self, key: str, headings: List[str], values: List[List], disabled: bool
    ):

        _table = self._get_table(headings, [[]])
        _layout = _table.layout(self._prefixf(key))
        if not disabled:
            _layout = [[sg.Push(), sg.Button("Save", key="save")]] + _layout
        window = sg.Window(
            "MUSE",
            layout=_layout,
            finalize=True,
            font="roman 16",
            resizable=True,
            auto_size_buttons=True,
            auto_size_text=True,
        )
        w, h = window.size
        window.set_min_size((max(512, w), max(256, h)))
        _table.disabled = disabled
        _table.values = values
        _table.bind_handlers()
        try:
            while True:
                event, _ = window.read()
                print(event)
                if event == sg.WIN_CLOSED or event == "Exit":
                    break
                if event == "save":
                    _table.commit()
                    return _table.values
                if _table.should_handle_event(event):
                    _table(window, event, values)
                else:
                    print("Unhandled event in table window ", event)

            return values
        finally:
            window.close()


class TechnologyView(TwoColumnMixin, BaseView):
    def __init__(self, model: Datastore):
        super().__init__("technology")
        self._datastore = model
        self._model = model.process
        self.model = TechnologyModelHelper(model)

        self.TABLE_VALUES = {
            "cost": [[]],
            "capacity": [[]],
            "input": [[]],
            "output": [[]],
            "agent": [[]],
            "existing_capacity": [[]],
        }

        # Widgets
        self._tech_info = TechnologyInfo()
        self._tech_tables = TechnologyTables(
            tab_headings=[x for x in self.TABLE_VALUES] + ["demand"]
        )
        self._tech_list = ListboxWithButtons()
        self._save_edit_btns = SaveEditButtons()

        # Internal State
        self._selected = -1

        self._years = []
        self._commin = []
        self._commout = []
        self._regions = []

        self._current_key = None
        self._editing = None

        self._current_process = None

    def enable_editing(self, window, force=False):
        # Careful, If enabled, form should be disabled
        # and vice versa
        if not self._editing or force:
            # Enable info and table
            self._tech_info.enable_editing(window, force)
            self._tech_tables.disabled = False
            self._edit_year_btn.update(disabled=False)
            # Disable list on the left
            self._tech_list.disabled = True
            self._editing = True

    def disable_editing(self, window, force=False):
        if self._editing or force:
            # Disable info and table
            self._tech_info.disable_editing(window, force)
            self._tech_tables.disabled = True
            self._edit_year_btn.update(disabled=True)
            # Enable the list
            self._tech_list.disabled = False
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

    def get_current_process(self):
        return self._current_process

    def set_current_process(self, window, _process):
        self._current_process = _process
        self._update_fields_for_process(window, _process)

    def get_current_process_id(self):
        # Should be used only when not in edit mode
        _processes = self.model.processes
        return _processes[self.selected]

    def _update_list(self, _processes):
        self._tech_list.values = _processes
        self.selected = min(self.selected, len(_processes) - 1)
        self._tech_list.indices = [self.selected] if self.selected != -1 else None

    def _update_info(self, window, _process: Process):
        self._tech_info.update(window, _process)

    def _get_table_values_for_process(self, _process: Process):
        _fuel = _process.fuel
        _enduse = _process.end_use
        # Year region cartesian product
        year_region = [(x, y) for x in self._years for y in self._regions]

        _values = {}

        _available_year_region = [
            (x, y) for x in self.model.available_years for y in self._regions
        ]
        _values["existing_capacity"] = self.model.get_existing_capacity_for_process(
            _process, _available_year_region
        )

        _values["capacity"] = self.model.get_capacity_for_process(_process, year_region)

        _values["cost"] = self.model.get_cost_for_process(_process, year_region)

        _values["input"] = self.model.get_commin_table_for_process(
            _process,
            year_region,
            [_fuel] + self._commin,
        )

        _values["output"] = self.model.get_commout_table_for_process(
            _process, year_region, [_enduse] + self._commout
        )

        _values["agent"] = self.model.get_agent_table_for_process(
            _process,
            year_region,
            self.model.get_agent_share_map_for_regions(self._regions),
        )
        return _values

    def _read_tables(self):
        for k in FIXED_TABLES:
            self.TABLE_VALUES[k] = self._tech_tables.read(k)

    def _patch_tables(self, _process: Process):
        # Read UI Tables
        self._read_tables()

        # Read process tables
        _values = self._get_table_values_for_process(_process)

        # Paste UI tables on top of process tables
        for k in _values:
            # If new values are empty, then nothing to patch
            if _values[k] == [[]] or self.TABLE_VALUES[k] == [[]]:
                continue
            # _values[k] is a list[list]
            # Convert current table into a dictionary indexed by year, region
            _tv = {(int(x[0]), str(x[1])): x[2:] for x in self.TABLE_VALUES[k]}
            for r in _values[k]:
                _key = (int(r[0]), str(r[1]))
                if _key in _tv:
                    r[2:] = _tv[_key]

        self.TABLE_VALUES = _values
        self._tech_tables.update(self.TABLE_VALUES)

    def _update_tables(self, _process: Process):
        # Update existing capacity
        # TODO: Add available years to table with missing values
        self.TABLE_VALUES = self._get_table_values_for_process(_process)
        self._tech_tables.update(self.TABLE_VALUES)

    def _update_fields_for_process(self, window, _process: Process):
        self._years = self.model.get_technodata_years_for_process(_process)
        self._regions = self.model.get_technodata_regions_for_process(_process)
        self._commin = self.model.get_additional_inputs_for_process(_process)
        self._commout = self.model.get_additional_outputs_for_process(_process)

        # Update tech info
        self._tech_info.update(window, _process)
        # Update tables
        self._update_tables(_process)

    def update(self, window):
        if self._editing == None:
            self.disable_editing(window, force=True)

        _processes = self.model.processes
        self._update_list(_processes)

        self._tech_info.set_preset_options(window, [None] + self.model.preset_sectors)
        self._tech_info.set_sector_options(window, self.model.standard_sectors)
        self._tech_info.set_commodity_options(window, self.model.commodities)

        if self.selected != -1:
            _tech_info = self.model.get_process(_processes[self.selected])
            self.set_current_process(window, _tech_info)

    def layout(self, prefix) -> List[List[Element]]:
        if not self._layout:
            self.prefix = prefix
            self._edit_year_btn = sg.Button(
                "Edit Year(s)", key=self._prefixf("edit_year")
            )
            # Left Column
            self.column_1 = sg.Col(
                self._tech_list.layout(self._prefixf()), expand_y=True
            )
            _btn_layout = self._save_edit_btns.layout(prefix=self._prefixf())
            _tech_info_layout = self._tech_info.layout(self._prefixf())
            _tech_table_layout = self._tech_tables.layout(self._prefixf("tables"))
            self.column_2 = sg.Col(
                _btn_layout
                + [[sg.HorizontalSeparator()]]
                + _tech_info_layout
                + [[self._edit_year_btn, sg.Push()]]
                + _tech_table_layout,
                expand_y=True,
                expand_x=True,
            )

            self._layout = [
                [self.column_1, self.column_2],
            ]
        return self._layout

    def bind_handlers(self):
        self._tech_info.bind_handlers()
        self._tech_tables.bind_handlers()
        self._save_edit_btns.bind_handlers()

    def __call__(self, window, event, values):
        print("Technology view handling - ", event)
        address = event
        if event[0] and isinstance(event[0], tuple):
            address = event[0]

        _event = address[len(self._prefixf()) :][0]

        if _event == "listbox":
            # Selection event
            indices = self._tech_list.indices
            if len(indices):
                self.selected = indices[0]
                self.update(window)
        elif _event == "edit":
            return self._handle_edit(window)
        elif _event == "add":
            return self._handle_add(window)
        elif _event == "delete":
            return self._handle_delete_process(window)
        elif _event == "save":
            return self._handle_save(window, values)
        elif _event == "edit_year":
            return self._handle_edit_year()
        elif _event == "edit_regions":
            return self._handle_edit_regions(window)
        elif _event == "edit_inputs":
            return self._handle_edit_inputs(window, values)
        elif _event == "edit_outputs":
            return self._handle_edit_outputs(window, values)
        elif _event == "tables":
            ret = self._tech_tables(window, event, values)
            if not ret:
                return

            print("Tables tabs returned", ret)
            if ret not in self.TABLE_VALUES:
                return

            # Save current table values from UI
            # if self._current_key in FIXED_TABLES:
            #    self.TABLE_VALUES[self._current_key].values = self._tech_tables.read(self._current_key)

            self._current_key = ret
            if ret in FIXED_TABLES:
                # self._tech_tables.show_table(ret, self.TABLE_VALUES[ret])
                return

            # Disable tab group
            self._tech_tables.disable_tabs(window)
            try:
                _headings = []

                _form_values = self._tech_info.read(values)
                if ret == "input":
                    _fuel = _form_values.get("fuel", "")
                    _headings = [_fuel] + [
                        x for x in self._commin if x.lower() != _fuel.lower()
                    ]

                elif ret == "output":
                    _end_use = _form_values.get("end_use", "")
                    _headings = [_end_use] + [
                        x for x in self._commout if x.lower() != _end_use.lower()
                    ]

                elif ret == "agent":
                    _headings = list(
                        self.model.get_agent_share_map_for_regions(
                            self._regions
                        ).values()
                    )
                else:
                    raise ValueError("Unknown value")
                # Show next table
                _values = self._tech_tables.show_table(
                    self._current_key,
                    self.TABLE_VALUES[self._current_key],
                    _headings,
                    not self._editing,
                )
                self.TABLE_VALUES[self._current_key] = _values
            finally:
                self._tech_tables.enable_tabs(window)

    def _convert_tables_to_models(self, current_values: Dict[str, Any]):
        # comm_in, comm_out
        all_commodities = self.model.commodities
        _fuel = next(
            (x for x in all_commodities if x.lower() == current_values["fuel"].lower()),
            "",
        )
        _end_use = next(
            (
                x
                for x in all_commodities
                if x.lower() == current_values["end_use"].lower()
            ),
            "",
        )
        comm_in = [_fuel] + [x for x in self._commin if x.lower() != _fuel.lower()]
        comm_out = [_end_use] + [
            x for x in self._commout if x.lower() != _end_use.lower()
        ]

        current_values["comm_in"] = [
            CommodityFlow(
                commodity=comm_in[i],
                level="fixed",
                region=x[1],
                timeslice=x[0],
                value=v,
            )
            for x in self.TABLE_VALUES["input"]
            for i, v in enumerate(x[2:])
        ]

        current_values["comm_out"] = [
            CommodityFlow(
                commodity=comm_out[i],
                level="fixed",
                region=x[1],
                timeslice=x[0],
                value=v,
            )
            for x in self.TABLE_VALUES["output"]
            for i, v in enumerate(x[2:])
        ]

        # Normalize keys to str, str as reading from
        # UI may result in str, str and from model
        # may result in int, str
        keyed_cost = {
            (str(x[0]), x[1]): Cost(
                cap_par=x[2],
                cap_exp=x[3],
                fix_par=x[4],
                fix_exp=x[5],
                var_par=x[6],
                var_exp=x[7],
                interest_rate=x[8],
            )
            for x in self.TABLE_VALUES["cost"]
            if x
        }
        keyed_utilisation = {
            (str(x[0]), x[1]): Utilisation(
                utilization_factor=x[-2],
                efficiency=x[-1],
            )
            for x in self.TABLE_VALUES["capacity"]
            if x
        }

        keyed_capacity = {
            (str(x[0]), x[1]): Capacity(
                max_capacity_addition=x[2],
                max_capacity_growth=x[3],
                total_capacity_limit=x[4],
                technical_life=x[5],
                scaling_size=x[6],
            )
            for x in self.TABLE_VALUES["capacity"]
            if x
        }
        keyed_agents = {}
        _share_names = self.model.get_agent_share_map_for_regions(self._regions)
        for x in self.TABLE_VALUES["agent"]:
            if len(x) == 0:
                continue
            _x_year, _x_region = str(x[0]), x[1]
            _key = (_x_year, _x_region)
            keyed_agents[_key] = []

            # Get retrofit agent with share name
            for (v, k) in zip(x[2:], _share_names):
                if not v:
                    continue
                _name, _type, _ = k
                capacity_share = CapacityShare(
                    agent_name=_name, agent_type=_type, region=_x_region, share=v
                )
                keyed_agents[_x_year, _x_region].append(capacity_share)

        # technodatas
        # cost, capacity, utilisation
        year_region = [
            (str(year), region) for year in self._years for region in self._regions
        ]
        current_values["technodatas"] = [
            Technodata(
                time=x[0],
                region=x[1],
                cost=keyed_cost[x],
                utilisation=keyed_utilisation[x],
                capacity=keyed_capacity[x],
                agents=keyed_agents[x],
            )
            for x in year_region
        ]

        # TODO Values are being discarded if missing
        current_values["existing_capacities"] = [
            ExistingCapacity(region=x[1], year=x[0], value=x[2])
            for x in self.TABLE_VALUES["existing_capacity"]
            if x and x[2]
        ]
        return current_values

    def _handle_edit_year(self):
        # Current years
        current_years = self._years[:]

        # Get all years
        available_years = self.model.available_years

        _, self._years = show_dual_listbox(
            "Data Years",
            v_one=sorted([x for x in available_years if x not in current_years]),
            v_two=sorted(self._years),
        )

        self._years = [int(x) for x in self._years]

        # Get associated years
        self._patch_tables(self.get_current_process())

    def _handle_add(self, window):
        # Create a default process
        technology = sg.popup_get_text(
            "Please enter name of technology to add",
            "Add Technology",
            "New Technology 1",
        )
        if technology == None or technology.strip() == "":
            return None, "0 technologies added"

        # and update view
        technology = technology.strip()
        _process = DummyProcess(
            name=technology,
            sector="",
            preset_sector=None,
            fuel="",
            end_use="",
            type="energy",
            technodatas=[],
            demands=[],
            existing_capacities=[],
            comm_in=[],
            comm_out=[],
            capacity_unit="PJ/y",
        )

        _processes = self.model.processes
        _processes.append(technology)
        self.selected = inf
        self._update_list(_processes)
        self.set_current_process(window, _process)

        # Set all regions
        self._regions = self.model.regions
        self._tech_info.set_regions(window, self._regions)
        self._patch_tables(_process)
        # Simulate edit mode
        return self._handle_edit(window)

    def _handle_save(self, window, values):
        # Commit to datastore

        # Get current values from view
        self._read_tables()
        _values = self._tech_info.read(values)

        # Handle preset_sector case
        # TODO move this to process model as santisation step?
        _preset_sector = _values.pop("preset_sector", None)
        if not _preset_sector or _preset_sector == "None":
            # Empty string, None, or 'None' should be None
            _preset_sector = None
        _values["preset_sector"] = _preset_sector

        # Get name in the form
        new_name = _values["name"]

        # Check if it is add mode / edit mode
        _ids = self.model.processes

        if self.selected == len(_ids):
            # Add mode
            try:
                _values = self._convert_tables_to_models(_values)
                # TODO: Move it out.
                _values["demands"] = []
                _values["capacity_unit"] = "PJ/y"
                process = Process.parse_obj(_values)
                self._model.create(process)
            except KeyAlreadyExists:
                raise SaveException(
                    f'Technology with name "{new_name}" already exists!'
                )
            except Exception as e:
                raise SaveException() from e
        else:
            # Update mode
            # Get current model key
            _process_id = self.get_current_process_id()
            _process = self.get_current_process()

            if new_name != _process.name:
                deps = self._model.forward_dependents(_process)
                for d in deps:
                    if len(deps[d]):
                        # Not supporting name change for ones with forward deps
                        raise SaveException() from RuntimeError(
                            "Changing name is not supported for technologies already associated with resources"
                        )

            _model_dict = _process.dict()
            try:
                _values = self._convert_tables_to_models(_values)
                _model_dict.update(_values)
                _updated_process = Process.parse_obj(_model_dict)
                self._model.update(_process_id, _updated_process)
                # Fingers crossed
            except Exception as e:
                print(e)
                raise SaveException() from e

        # Disable save, enable edit
        self._save_edit_btns.state = "idle"
        self.disable_editing(window)

        self.update(window)
        # Communicate save mode to parent
        return "idle", self.key

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

    def _handle_edit_inputs(self, window, values):
        current_comm_in = self._commin[:]

        # In editing mode - so fuel / end use can change
        # after inital value - so read from UI
        _values = self._tech_info.read(values)
        all_commodities = self.model.commodities

        comm_in_with_fuel = [_values.get("fuel", "").lower()] + [
            x.lower() for x in self._commin
        ]
        _, self._commin = show_dual_listbox(
            "CommIn",
            v_one=[x for x in all_commodities if x.lower() not in comm_in_with_fuel],
            v_two=self._commin,
        )

        self._tech_info.set_inputs(window, self._commin)

        # Read table from UI
        self._read_tables()

        if self.TABLE_VALUES["input"] == [[]]:
            return

        # Expand / Contract / Reorder table columns
        # Based on comm_in order
        _table = self.TABLE_VALUES["input"]

        columns = list(zip(*self.TABLE_VALUES["input"]))
        empty_column = ["" for _ in range(len(_table))]
        comm_in_map = {x: columns[i + 3] for i, x in enumerate(current_comm_in)}
        self.TABLE_VALUES["input"] = list(
            zip(
                *(
                    [columns[0], columns[1], columns[2]]
                    + [
                        comm_in_map[x] if x in comm_in_map else empty_column
                        for x in self._commin
                    ]
                )
            )
        )
        self._tech_tables.update({"input": self.TABLE_VALUES["input"]})

    def _handle_edit_outputs(self, window, values):
        current_comm_out = self._commout[:]
        all_commodities = self.model.commodities
        _values = self._tech_info.read(values)
        comm_out_with_end_use = [_values.get("end_use", "").lower()] + [
            x.lower() for x in self._commout
        ]
        _, self._commout = show_dual_listbox(
            "CommOut",
            v_one=[
                x for x in all_commodities if x.lower() not in comm_out_with_end_use
            ],
            v_two=self._commout,
        )
        self._tech_info.set_outputs(window, self._commout)

        self._read_tables()
        if self.TABLE_VALUES["output"] == [[]]:
            return

        # Expand / Contract / Reorder table columns
        # Based on comm_in order
        _table = self.TABLE_VALUES["output"]

        columns = list(zip(*_table))
        empty_column = ["" for _ in range(len(_table))]
        comm_out_map = {x: columns[i + 3] for i, x in enumerate(current_comm_out)}
        self.TABLE_VALUES["output"] = list(
            zip(
                *(
                    [columns[0], columns[1], columns[2]]
                    + [
                        comm_out_map[x] if x in comm_out_map else empty_column
                        for x in self._commout
                    ]
                )
            )
        )
        self._tech_tables.update({"output": self.TABLE_VALUES["output"]})

    def _handle_edit_regions(self, window):
        _process = self.get_current_process()
        all_regions = self.model.regions

        _, self._regions = show_dual_listbox(
            "Regions",
            v_one=[x for x in all_regions if x not in self._regions],
            v_two=self._regions,
        )
        self._tech_info.set_regions(window, self._regions)
        self._patch_tables(_process)

    def _handle_delete_process_safe(self, id):
        """
        Internal function that deletes the technology
        returns True / False based on whether technology was deleted or not
        """
        _process = self.model.get_process(id)

        # Compute forward dependencies
        deps = self._model.forward_dependents_recursive(_process)

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
                f"Deleting technology {id} will result in the following being deleted:\n",
                f"{dep_string}" f"Delete anyway?\n",
                title="Warning!",
            )
            if ret and ret == "Yes":
                self._model.delete(id)
                return True
            else:
                return False
        else:
            self._model.delete(id)
            return True

    def _handle_delete_process(self, window):
        if self.selected == -1:
            return None, "Select a technology before attempting to delete!"

        _process_id = self.get_current_process_id()

        is_deleted = self._handle_delete_process_safe(_process_id)
        if not is_deleted:
            return
        self._selected = max(0, self._selected - 1)
        self.update(window)
        return None, f'Technology "{_process_id}" deleted'
