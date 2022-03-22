from functools import partial
from typing import List
import PySimpleGUI as sg
from PySimpleGUI import Element

from muse_gui.backend.resources.datastore import Datastore
from muse_gui.frontend.widgets.table import FixedColumnTable
from ...backend.data.agent import Agent, AgentType
from ..widgets.listbox import ListboxWithButtons
from ..widgets.form import Form
from .base import BaseView, TwoColumnMixin

class AgentRepository():
    def __init__(self, model: Datastore):
        self._parent_model = model
        self._model = model.agent
        self._agents = {}

    def refresh(self):
        _agent_ids = self._model.list()
        self._agents = {}
        for _id in _agent_ids:
            _agent = self._model.read(_id)
            _name, _type, _region = _agent.name, _agent.type, _agent.region
            if _name not in self._agents:
                self._agents[_name] = {}

            if _type not in self._agents[_name]:
                self._agents[_name][_type] = {}

            self._agents[_name][_type][_region] = _agent

    def list(self):
        return list(self._agents.keys())

    def get(self, name: str):
        new_agent = self._agents[name].get('New', {})
        retro_agent = self._agents[name].get('Retrofit', {})

        for r in retro_agent:
            if r not in new_agent:
                _agent = retro_agent[r]
                new_agent = Agent(**_agent.dict())
                new_agent.type = AgentType.NEW
                new_agent.share = f'{name}_new'

                self._model.create(new_agent)
                self._agents[name]['New'][r] = new_agent

        for r in new_agent:
            if r not in retro_agent:
                _agent = new_agent[r]
                retro_agent = Agent(**_agent.dict())
                retro_agent.type = AgentType.RETROFIT
                retro_agent.share = f'{name}'

                self._model.create(retro_agent)
                self._agents[name]['Retrofit'][r] = retro_agent

        return (new_agent, retro_agent)
    def get_sectors(self):
        return [
            x
            for x in self._parent_model.sector.list()
            if self._parent_model.sector.read(x).type == 'standard'
        ]

class AgentView(TwoColumnMixin, BaseView):
    def __init__(self, model: Datastore):
        super().__init__('agent')
        self._parent_model = model
        self.model = AgentRepository(model)

        self._agent_list = partial(
            ListboxWithButtons
        )
        self._agent_name = partial(
            sg.Input,
            size=(20, 1),
        )
        self._agent_sector = partial(
            sg.OptionMenu,
            [None],
            size=(18, 1)
        )

        _params = ['Region', 'DecisionMethod', 'SearchRule', 'Quantity', 'Budget', 'Maturity Threshold']
        _ncols = len(_params)
        self._new_agent_info = partial(
            FixedColumnTable,
            1,
            _ncols,
            1,
            pad=0,
            values=[[]],
            headings=_params,
            expand_x=True, expand_y=True,
            select_mode=sg.TABLE_SELECT_MODE_NONE,
            enable_click_events=True,
        )
        self._retro_agent_info = partial(
            FixedColumnTable,
            1,
            _ncols,
            1,
            pad=0,
            values=[[]],
            headings=_params,
            expand_x=True, expand_y=True,
            select_mode=sg.TABLE_SELECT_MODE_NONE,
            enable_click_events=True,
        )
        self._selected = -1

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

    def update(self, window=None):
        self.model.refresh()

        _agents = self.model.list()
        self._agent_list.update(_agents)

        self.selected = min(self.selected, len(_agents) - 1)
        self._agent_list.indices = [self.selected] if self.selected != -1 else None

        if self.selected != -1:
            _agent_name = _agents[self.selected]
            _new_agent, _retro_agent = self.model.get(_agent_name)

            # _prices = _commodity_info.commodity_prices
            # _values = [[p.time, p.region_name, p.value] for p in _prices]
            # self._prices_table.values = _values
            # Update agent name
            self._agent_name(_agent_name)

            # Update available sector options
            _sectors = self.model.get_sectors()
            self._agent_sector.update(values=_sectors)

            # Update new agent info
            _values = [
                [
                    v.region,
                    v.decision_method,
                    v.search_rule,
                    v.quantity,
                    v.budget,
                    v.maturity_threshold,
                ] for v in _new_agent.values()
            ]
            self._new_agent_info.values = _values

            # Update retro agent info
            _values = [
                [
                    v.region,
                    v.decision_method,
                    v.search_rule,
                    v.quantity,
                    v.budget,
                    v.maturity_threshold,
                ] for v in _retro_agent.values()
            ]
            self._retro_agent_info.values = _values

    def layout(self, prefix) -> List[List[Element]]:
        if not self._layout:
            self.prefix = prefix
            # Left
            self._agent_list = self._agent_list()

            self.column_1 = sg.Col(
                self._agent_list.layout(self._prefixf()),
                expand_y=True
            )

            # Right
            self._new_agent_info = self._new_agent_info()
            self._retro_agent_info = self._retro_agent_info()

            self._agent_name = self._agent_name(key=self._prefixf('name'))
            self._agent_sector = self._agent_sector(key=self._prefixf('sector'))

            _agent_info_layout = [
                [
                    sg.Text(f'Name', size=(6, 1)),
                    sg.Text(':', auto_size_text=True),
                    self._agent_name
                ],
                [
                    sg.Text('Sector', size=(6, 1)),
                    sg.Text(':', auto_size_text=True),
                    self._agent_sector
                ],
            ]


            _new_agent_layout = self._new_agent_info.layout(
                self._prefixf('new'),
            )
            _retro_agent_layout = self._retro_agent_info.layout(
                self._prefixf('retrofit'),
            )

            _details = sg.Frame('Details', [
                [
                    sg.Text('Retrofit', auto_size_text=True),
                    sg.HorizontalSeparator()
                ],
            ] + _new_agent_layout + [
                [
                    sg.Text('')
                ],
                [
                    sg.Text('New', auto_size_text=True),
                    sg.HorizontalSeparator()
                ],
            ] + _retro_agent_layout,
                expand_x=True, expand_y=True)
            self.column_2 = sg.Col(
                _agent_info_layout + [
                    [
                        sg.Text('')
                    ],
                    [
                        _details
                    ]
                ],expand_x=True, expand_y=True)
            self._layout = [
                [self.column_1, self.column_2],
            ]
        return self._layout

    def bind_handlers(self):
        self._new_agent_info.bind_handlers()
        self._retro_agent_info.bind_handlers()


    def __call__(self, window, event, values):
        print('Agent view handling - ', event)
        address = event
        if event[0] and isinstance(event[0], tuple):
            address = event[0]

        _event = address[len(self._prefixf()):][0]

        if _event == 'listbox':
            # Selection event
            indices = self._agent_list.indices
            if len(indices):
                self.selected =  indices[0]
                self.update(window)
        elif _event == 'new':
            self._new_agent_info(window, event, values)
        elif _event == 'retrofit':
            self._retro_agent_info(window, event, values)
        pass