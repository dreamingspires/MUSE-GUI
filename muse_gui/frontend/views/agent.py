import textwrap
from math import inf
from typing import Any, Dict, List, Optional

import PySimpleGUI as sg
from PySimpleGUI import Element

from muse_gui.backend.resources.datastore import Datastore
from muse_gui.backend.resources.datastore.exceptions import KeyAlreadyExists
from muse_gui.frontend.popups import show_dual_listbox
from muse_gui.frontend.views.exceptions import SaveException
from muse_gui.frontend.widgets.base import BaseWidget
from muse_gui.frontend.widgets.button import SaveEditButtons
from muse_gui.frontend.widgets.table import FixedColumnTable

from ...backend.data.agent import (
    Agent,
    AgentData,
    AgentObjective,
    AgentType,
    ObjectiveType,
)
from ..widgets.form import Form
from ..widgets.listbox import ListboxWithButtons
from .base import BaseView, TwoColumnMixin

AGENT_TABLE_HEADINGS = {
    "new_objectives": [
        "Obj1",
        "Obj1Weight",
        "Obj1Maximize?",
        "Obj2",
        "Obj2Weight",
        "Obj2Maximize?",
        "Obj3",
        "Obj3Weight",
        "Obj3Maximize?",
    ],
    "retrofit_objectives": [
        "Obj1",
        "Obj1Weight",
        "Obj1Maximize?",
        "Obj2",
        "Obj2Weight",
        "Obj2Maximize?",
        "Obj3",
        "Obj3Weight",
        "Obj3Maximize?",
    ],
    "new_params": [
        "Share",
        "DecisionMethod",
        "SearchRule",
        "Quantity",
        "Budget",
        "M. Threshold",
    ],
    "retrofit_params": [
        "Share",
        "DecisionMethod",
        "SearchRule",
        "Quantity",
        "Budget",
        "M. Threshold",
    ],
}


class AgentModelHelper:
    def __init__(self, model: Datastore):
        self._parent_model = model
        self._agent = model.agent
        self._sector = model.sector
        self._region = model.region

    @property
    def regions(self):
        return self._region.list()

    @property
    def agents(self):
        return self._agent.list()

    @property
    def sectors(self):
        return self._sector.list()

    @property
    def standard_sectors(self):
        return [x for x in self.sectors if self._sector.read(x).type == "standard"]

    def get_agent(self, id: str):
        return self._agent.read(id)

    def get_regions_for_agent(self, _agent: Agent):
        return sorted(
            list(
                dict.fromkeys(
                    x for x in (list(_agent.new.keys()) + list(_agent.retrofit.keys()))
                )
            )
        )

    def get_sectors_for_agent(self, _agent: Agent):
        return sorted(list(dict.fromkeys(x for x in _agent.sectors)))

    def get_data_for_agent(self, _agent: Agent, rows: List[str]):
        if len(rows) == 0:
            return {"New": [[]], "Retrofit": [[]]}
        NCOLS = 15
        _values = {"New": {}, "Retrofit": {}}
        for r, _agent_data in _agent.new.items():
            region = r
            _type = "New"
            params = [
                _agent_data.share,
                _agent_data.decision_method,
                _agent_data.search_rule,
                _agent_data.quantity,
                _agent_data.budget,
                _agent_data.maturity_threshold,
            ]
            for obj in (
                _agent_data.objective_1,
                _agent_data.objective_2,
                _agent_data.objective_3,
            ):
                if obj:
                    params.extend(
                        [obj.objective_type, obj.objective_data, obj.objective_sort]
                    )
                else:
                    params.extend(["", "", ""])

            _values[_type][region] = params

        for r, _agent_data in _agent.retrofit.items():
            region = r
            _type = "Retrofit"
            params = [
                _agent_data.share,
                _agent_data.decision_method,
                _agent_data.search_rule,
                _agent_data.quantity,
                _agent_data.budget,
                _agent_data.maturity_threshold,
            ]
            for obj in (
                _agent_data.objective_1,
                _agent_data.objective_2,
                _agent_data.objective_3,
            ):
                if obj:
                    params.extend(
                        [obj.objective_type, obj.objective_data, obj.objective_sort]
                    )
                else:
                    params.extend(["", "", ""])

            _values[_type][region] = params

        sort_keys = sorted(rows)
        return {
            t: [
                [k] + (_values[t][k] if k in _values[t] else ["" for _ in range(NCOLS)])
                for k in sort_keys
            ]
            for t in _values
        }


class AgentInfo(BaseWidget):
    def __init__(self, key: Optional[str] = None):
        super().__init__(key)

        self._editing = None

    def enable_editing(self, window, force=False):
        if not self._editing or force:
            # Enable form fields
            window[self._prefixf("name")](disabled=False)
            window[self._prefixf("sectors")](disabled=False)
            window[self._prefixf("edit_sectors")](disabled=False)

            self._editing = True

    def disable_editing(self, window, force=False):
        if self._editing or force:
            # Enable form fields
            window[self._prefixf("name")](disabled=True)
            window[self._prefixf("sectors")](disabled=True)
            window[self._prefixf("edit_sectors")](disabled=True)

            self._editing = False

    def _set_textbox_with_list(self, window, key: str, val: List):
        _text = ",".join(val)
        _text = textwrap.fill(_text, 20, max_lines=2, placeholder="...")
        window[self._prefixf(key)](_text)

    def set_sectors(self, window, val):
        self._set_textbox_with_list(window, "sectors", val)

    def bind_handlers(self):
        pass

    def update(self, window, _agent: Agent):

        # Update name
        window[self._prefixf("name")].update(value=_agent.name)

        # Update list of sectors
        _sectors = sorted(list(dict.fromkeys(x for x in _agent.sectors)))
        self.set_sectors(window, _sectors)

    def layout(self, prefix):
        if not self._layout:
            self.prefix = prefix

            # Layout form
            _layout = [
                [
                    sg.Text("Name", size=(6, 1)),
                    sg.Text(":", auto_size_text=True),
                    sg.Input("", size=(20, 1), key=self._prefixf("name")),
                    sg.Frame(
                        "Sectors",
                        [
                            [
                                sg.Multiline(
                                    "",
                                    size=(20, 2),
                                    disabled=True,
                                    write_only=True,
                                    no_scrollbar=True,
                                    key=self._prefixf("sectors"),
                                ),
                                sg.Button("Change", key=self._prefixf("edit_sectors")),
                            ]
                        ],
                        element_justification="center",
                    ),
                ]
            ]
            self._layout = [[sg.Column(_layout)]]
        return self._layout


class AgentTables(BaseWidget):
    def __init__(self, tab_headings: List[str], key: Optional[str] = None):
        super().__init__(key)
        self._tab_headings = tab_headings
        self._tables = self._create_tables()
        self._disabled = False

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
            _table_layout = []
            for h in self._tab_headings:
                _agent_table_layout = []
                for k in self._tables:
                    if k.endswith(h.lower()):
                        _agent_table_layout += [
                            [
                                sg.Text(k.split("_", 1)[0].title()),
                                sg.HorizontalSeparator(),
                            ]
                        ]
                        _agent_table_layout += self._tables[k].layout(self._prefixf(k))

                _table_layout.append(
                    [sg.Tab(h.replace("_", " ").title(), _agent_table_layout)]
                )

            self._tabgroup = sg.TabGroup(
                _table_layout,
                expand_x=True,
                expand_y=True,
                enable_events=True,
                key=self._prefixf("tabs"),
            )
            self._layout = [[self._tabgroup]]
        return self._layout

    def _get_table(self, headings: List[str], values=[[]]) -> FixedColumnTable:
        _headings = ["Region"] + headings
        return FixedColumnTable(
            0,
            len(_headings),
            1,
            pad=0,
            values=values,
            headings=_headings,
            expand_x=True,
            expand_y=True,
            select_mode=sg.TABLE_SELECT_MODE_NONE,
            enable_click_events=True,
        )

    def _create_tables(self) -> Dict[str, FixedColumnTable]:
        return {
            k: self._get_table(AGENT_TABLE_HEADINGS[k]) for k in AGENT_TABLE_HEADINGS
        }

    def read(self, key: str):
        return self._tables[key].values

    def __call__(self, window, event, values):
        print("Agent tables view handling - ", event)
        address = event
        if event[0] and isinstance(event[0], tuple):
            address = event[0]

        _event = address[len(self._prefixf()) :][0]

        if _event in self._tables:
            self._tables[_event](window, event, values)
            return None

        if _event == "tabs":
            # Tab switch event
            tab_name = values[self._prefixf("tabs")]
            if tab_name:
                return tab_name.lower().replace(" ", "_")


class AgentView(TwoColumnMixin, BaseView):
    def __init__(self, model: Datastore):
        super().__init__("agent")
        self._datastore = model
        self._model = model.agent
        self.model = AgentModelHelper(model)

        self._agent_list = ListboxWithButtons()
        self._save_edit_btns = SaveEditButtons()
        self._agent_info = AgentInfo()
        self._agent_tables = AgentTables(
            tab_headings=["params", "objectives"],
        )

        # Internal state
        self.TABLE_VALUES = {
            "new_params": [[]],
            "new_objectives": [[]],
            "retrofit_params": [[]],
            "retrofit_objectives": [[]],
        }
        self._selected = -1
        self._sectors = []
        self._regions = []

        self._current_key = None
        self._editing = None
        self._current_agent = None

    def enable_editing(self, window, force=False):
        # Careful, If enabled, form should be disabled
        # and vice versa
        if not self._editing or force:
            # Enable info and table
            self._agent_info.enable_editing(window, force)
            self._agent_tables.disabled = False
            self._edit_region_btn.update(disabled=False)
            # Disable list on the left
            self._agent_list.disabled = True
            self._editing = True

    def disable_editing(self, window, force=False):
        if self._editing or force:
            # Disable info and table
            self._agent_info.disable_editing(window, force)
            self._agent_tables.disabled = True
            self._edit_region_btn.update(disabled=True)
            # Enable the list
            self._agent_list.disabled = False
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

    def get_current_agent(self):
        return self._current_agent

    def get_current_agent_id(self):
        # Should be used only when not in edit mode
        _agents = self.model.agents
        return _agents[self.selected]

    def set_current_agent(self, window, _agent: Agent):
        self._current_agent = _agent
        self._update_fields(window, _agent)

    def _get_table_values_for_agent(self, _agent: Agent):

        _values = self.model.get_data_for_agent(_agent, self._regions)
        _new = _values.get("New", [[]])
        _retrofit = _values.get("Retrofit", [[]])

        _new_objectives = [[]]
        _new_params = [[]]
        if _new != [[]]:
            _new_params = [r[:7] for r in _new]
            _new_objectives = [r[0:1] + r[7:] for r in _new]

        _retrofit_objectives = [[]]
        _retrofit_params = [[]]
        if _retrofit != [[]]:
            _retrofit_params = [r[:7] for r in _retrofit]
            _retrofit_objectives = [r[0:1] + r[7:] for r in _retrofit]

        return {
            "new_params": _new_params,
            "new_objectives": _new_objectives,
            "retrofit_params": _retrofit_params,
            "retrofit_objectives": _retrofit_objectives,
        }

    def _read_tables(self):
        for k in self.TABLE_VALUES:
            self.TABLE_VALUES[k] = self._agent_tables.read(k)

    def _patch_tables(self, _agent: Agent):
        # Read UI Tables
        self._read_tables()

        # Read process tables
        _values = self._get_table_values_for_agent(_agent)

        # Paste UI tables on top of agent tables
        for k in _values:
            # If new values are empty, then nothing to patch
            if _values[k] == [[]] or self.TABLE_VALUES[k] == [[]]:
                continue
            # _values[k] is a list[list]
            # Convert current table into a dictionary indexed by year, region
            _tv = {x[0]: x[1:] for x in self.TABLE_VALUES[k]}
            for r in _values[k]:
                _key = r[0]
                if _key in _tv:
                    r[1:] = _tv[_key]

        self.TABLE_VALUES = _values
        self._agent_tables.update(self.TABLE_VALUES)

    def _update_tables(self, _agent: Agent):
        self.TABLE_VALUES = self._get_table_values_for_agent(_agent)
        self._agent_tables.update(self.TABLE_VALUES)

    def _update_list(self, _agents: List[str]):
        self._agent_list.values = _agents
        self.selected = min(self.selected, len(_agents) - 1)
        self._agent_list.indices = [self.selected] if self.selected != -1 else None

    def _update_info(self, window, _agent: Agent):
        self._agent_info.update(window, _agent)

    def _update_fields(self, window, _agent: Agent):
        self._sectors = self.model.get_sectors_for_agent(_agent)
        self._regions = self.model.get_regions_for_agent(_agent)

        # Update agent info
        self._agent_info.update(window, _agent)
        # Update tables
        self._update_tables(_agent)

    def update(self, window):
        if self._editing == None:
            self.disable_editing(window, force=True)

        _agents = self.model.agents
        self._update_list(_agents)

        if self.selected != -1:
            _agent_info = self.model.get_agent(self.get_current_agent_id())
            self.set_current_agent(window, _agent_info)

    def layout(self, prefix) -> List[List[Element]]:
        if not self._layout:
            self.prefix = prefix
            # Left
            self._edit_region_btn = sg.Button(
                "Edit Region(s)", key=self._prefixf("edit_regions")
            )
            self.column_1 = sg.Col(
                self._agent_list.layout(self._prefixf()), expand_y=True
            )
            _btn_layout = self._save_edit_btns.layout(prefix=self._prefixf())
            _info_layout = self._agent_info.layout(self._prefixf())
            _table_layout = self._agent_tables.layout(self._prefixf("tables"))
            self.column_2 = sg.Col(
                _btn_layout
                + [[sg.HorizontalSeparator()]]
                + _info_layout
                + [[self._edit_region_btn, sg.Push()]]
                + _table_layout,
                expand_y=True,
                expand_x=True,
            )

            self._layout = [
                [self.column_1, self.column_2],
            ]
        return self._layout

    def bind_handlers(self):
        self._agent_info.bind_handlers()
        self._agent_tables.bind_handlers()
        self._save_edit_btns.bind_handlers()

    def __call__(self, window, event, values):
        print("Agent view handling - ", event)
        address = event
        if event[0] and isinstance(event[0], tuple):
            address = event[0]

        _event = address[len(self._prefixf()) :][0]

        if _event == "listbox":
            # Selection event
            indices = self._agent_list.indices
            if len(indices):
                self.selected = indices[0]
                self.update(window)
        elif _event == "edit":
            return self._handle_edit(window)
        elif _event == "add":
            return self._handle_add(window)
        elif _event == "delete":
            return self._handle_delete_agent(window)
        elif _event == "save":
            return self._handle_save(window, values)
        elif _event == "edit_regions":
            return self._handle_edit_regions()
        elif _event == "edit_sectors":
            return self._handle_edit_sectors(window)
        elif _event == "tables":
            ret = self._agent_tables(window, event, values)
            print("Agent tables tab returned - ", ret)
            return

    def _convert_tables_to_models(self, current_values: Dict[str, Any]):
        for k in ["new", "retrofit"]:
            keyed_agent = {
                x[0]: AgentData(
                    num=None,
                    share=x[1],
                    decision_method=x[2],
                    search_rule=x[3],
                    quantity=x[4],
                    budget=x[5],
                    maturity_threshold=x[6],
                    objective_1=AgentObjective(
                        objective_type=y[1],
                        objective_data=y[2],
                        objective_sort=y[3],
                    ),
                    objective_2=AgentObjective(
                        objective_type=y[4],
                        objective_data=y[5],
                        objective_sort=y[6],
                    )
                    if y[4]
                    else None,
                    objective_3=AgentObjective(
                        objective_type=y[7],
                        objective_data=y[8],
                        objective_sort=y[9],
                    )
                    if y[7]
                    else None,
                )
                for x, y in zip(
                    self.TABLE_VALUES[f"{k}_params"],
                    self.TABLE_VALUES[f"{k}_objectives"],
                )
                if x and y
            }
            current_values[k] = {x: keyed_agent[x] for x in self._regions}
        return current_values

    def _handle_add(self, window):
        # Create a default process
        agent = sg.popup_get_text(
            "Please enter name of Agent to add",
            "Add Agent",
            "New Agent 1",
        )
        if agent == None or agent.strip() == "":
            return None, "0 agents added"

        # and update view
        agent = agent.strip()

        _agent = Agent(
            name=agent,
            sectors=[],
            new={},
            retrofit={},
        )

        _agents = self.model.agents
        _agents.append(agent)

        self.selected = inf
        self._update_list(_agents)
        self.set_current_agent(window, _agent)

        # Set all sectors
        self._sectors = self.model.standard_sectors
        self._agent_info.set_sectors(window, self._sectors)
        self._patch_tables(_agent)
        # Simulate edit mode
        return self._handle_edit(window)

    def _handle_save(self, window, values):
        # Get current values from view
        self._read_tables()
        _values = {
            "name": values[self._prefixf("name")],
            "sectors": self._sectors,
        }

        # Get name in the form
        new_name = _values["name"]

        # Check if it is add mode / edit mode
        _ids = self.model.agents

        if self.selected == len(_ids):
            # Add mode
            try:
                _values = self._convert_tables_to_models(_values)
                # TODO: Move it out.
                agent = Agent.parse_obj(_values)
                self._model.create(agent)
            except KeyAlreadyExists:
                raise SaveException(f'Agent with name "{new_name}" already exists!')
            except Exception as e:
                raise SaveException() from e
        else:
            # Update mode
            # Get current model key
            _agent_id = self.get_current_agent_id()
            _agent = self.get_current_agent()

            if new_name != _agent.name:
                deps = self._model.forward_dependents(_agent)
                for d in deps:
                    if len(deps[d]):
                        # Not supporting name change for ones with forward deps
                        raise SaveException() from RuntimeError(
                            "Changing name is not supported for agents already associated with resources"
                        )

            _model_dict = _agent.dict()
            try:
                _values = self._convert_tables_to_models(_values)
                _model_dict.update(_values)
                _updated_agent = Agent.parse_obj(_model_dict)
                self._model.update(_agent_id, _updated_agent)
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

    def _handle_edit_regions(self):
        all_regions = self.model.regions
        _, self._regions = show_dual_listbox(
            "Regions",
            v_one=[x for x in all_regions if x not in self._regions],
            v_two=self._regions,
        )
        self._patch_tables(self.get_current_agent())

    def _handle_edit_sectors(self, window):
        all_sectors = self.model.standard_sectors

        _, self._sectors = show_dual_listbox(
            "Sectors",
            v_one=[x for x in all_sectors if x not in self._sectors],
            v_two=self._sectors,
        )
        self._agent_info.set_sectors(window, self._sectors)

    def _handle_delete_agent_safe(self, id):
        """
        Internal function that deletes the Agent
        returns True / False based on whether Agent was deleted or not
        """
        _agent = self.model.get_agent(id)

        # Compute forward dependencies
        deps = self._model.forward_dependents_recursive(_agent)

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
                f"Deleting Agent {id} will result in the following being deleted:\n",
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

    def _handle_delete_agent(self, window):
        if self.selected == -1:
            return None, "Select an Agent before attempting to delete!"

        _id = self.get_current_agent_id()

        is_deleted = self._handle_delete_agent_safe(_id)
        if not is_deleted:
            return
        self._selected = max(0, self._selected - 1)
        self.update(window)
        return None, f'Agent "{_id}" deleted'
