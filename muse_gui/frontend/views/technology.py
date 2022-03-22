from functools import partial
from typing import List
import PySimpleGUI as sg
from PySimpleGUI import Element

from muse_gui.frontend.widgets.utils import render

from ...backend.resources.datastore import Datastore
from ...backend.data.process import Process

from ..widgets.listbox import ListboxWithButtons
from ..widgets.form import Form
from ..widgets.table import FixedColumnTable
from .base import TwoColumnMixin, BaseView

FIXED_TABLES = ['cost', 'capacity', 'existing_capacity']
class TechnologyView(TwoColumnMixin, BaseView):
    def __init__(self, model: Datastore):
        super().__init__('technology')
        self._parent_model = model
        self.model = model.process

        self._tech_list = partial(
            ListboxWithButtons
        )

        self._tech_info = partial(
            Form,
            Process
        )

        option_menu_f = partial(sg.OptionMenu, [None])

        self._render_fields = {
            'sector': option_menu_f,
            'fuel': option_menu_f,
            'end_use': option_menu_f,
        }

        self._selected = -1

        self.TABLE_HEADINGS_GEN = {
            'agent': lambda _process: list(dict.fromkeys(self.model.agent.read(x).share for x in self.model.process.read(_process).agents)),
            'capacity': lambda _process: ['Max Addition', 'Max Growth', 'Total Limit', 'Technical Life', 'Scaling Size', 'Utilisation Factor', 'Efficiency'],
            'cost': lambda _process: ['cap_par', 'cap_exp', 'fix_par', 'fix_exp', 'var_par', 'var_exp', 'Interest Rate'],
            'existing_capacity': lambda _process: ['Qty'],
            'input': lambda _process: [x.commodity for x in self.model.process.read(_process).comm_in],
            'output': lambda _process: [x.commodity for x in self.model.process.read(_process).comm_out],
        }
        self.TABLE_VALUES = {
            'agent': [[]],
            'capacity': [[]],
            'cost': [[]],
            'existing_capacity': [[]],
            'input': [[]],
            'output': [[]],
        }
        self._tables = self._create_tables()

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

    def update(self, window):
        _processes = self.model.list()

        self._tech_list.update(_processes)
        self.selected = min(self.selected, len(_processes) - 1)
        self._tech_list.indices = [self.selected] if self.selected != -1 else None

        if self.selected != -1:
            _tech_id = _processes[self.selected]
            _tech_info = self.model.read(_tech_id)

            # Update sectors
            _sectors = [
                x
                for x in self._parent_model.sector.list()
                if self._parent_model.sector.read(x).type == 'standard'
            ]
            window[self._prefixf('sector')].update(value=_tech_info.sector, values=_sectors)

            # Update fuel
            _commodities = [
                x
                for x in self._parent_model.commodity.list()
            ]
            window[self._prefixf('fuel')].update(value=_tech_info.fuel, values=_commodities)
            window[self._prefixf('end_use')].update(value=_tech_info.end_use, values=_commodities)

            # Update existing capacity
            _existing_capacity = [
                [x.year, x.region, x.value] for x in _tech_info.existing_capacities
            ]
            self._tables['existing_capacity'].values = _existing_capacity

            # Update capacity
            _capacity = [
                [
                    x.time,
                    x.region,
                    x.capacity.max_capacity_addition,
                    x.capacity.max_capacity_growth,
                    x.capacity.total_capacity_limit,
                    x.capacity.technical_life,
                    x.capacity.scaling_size,
                    x.utilisation.utilization_factor,
                    x.utilisation.efficiency,
                ] for x in _tech_info.technodatas
            ]
            self._tables['capacity'].values = _capacity

            # Update cost
            _cost = [
                [
                    x.time,
                    x.region,
                    x.cost.cap_par,
                    x.cost.cap_exp,
                    x.cost.fix_par,
                    x.cost.fix_exp,
                    x.cost.var_par,
                    x.cost.var_exp,
                    x.cost.interest_rate,
                ] for x in _tech_info.technodatas
            ]
            self._tables['cost'].values = _cost
            self._tech_info.update(window, _tech_info)

    def layout(self, prefix) -> List[List[Element]]:
        if not self._layout:
            self.prefix = prefix

            self._tech_list = self._tech_list()
            self._tech_info = self._tech_info()

            # Left Column
            self.column_1 = sg.Col(
                self._tech_list.layout(self._prefixf()),
                expand_y=True
            )

            _tech_info_layout = self._tech_info.layout(
                self._prefixf(),
                [
                    ['name' ],
                    ['type'],
                ]
            )

            _tech_options_layout = render(self._render_fields, _prefix=self._prefixf())

            _tech_table_layout = []
            for k in FIXED_TABLES:
                self._tables[k] = self._tables[k]()
                _tech_table_layout.append([sg.Tab(k.replace('_', ' ').title(), self._tables[k].layout(self._prefixf(k)))])

            _tech_table_layout = [[
                sg.TabGroup(_tech_table_layout, expand_x=True, expand_y=True)
            ]]
            self.column_2 = sg.Col(
                _tech_info_layout + _tech_options_layout + [[sg.Text('')]] + _tech_table_layout,
                expand_y=True, expand_x=True)

            self._layout = [
                [self.column_1, self.column_2],
            ]
        return self._layout

    def bind_handlers(self):
        for k in FIXED_TABLES:
            self._tables[k].bind_handlers()

    def __call__(self, window, event, values):
        print('Technology view handling - ', event)
        address = event
        if event[0] and isinstance(event[0], tuple):
            address = event[0]

        _event = address[len(self._prefixf()):][0]

        if _event == 'listbox':
            # Selection event
            indices = self._tech_list.indices
            if len(indices):
                self.selected = indices[0]
                self.update(window)

        elif _event in FIXED_TABLES:
            self._tables[_event](window, event, values)

        pass

    def _get_table(self, _type, _process=None):
        headings = ['Year', 'Region'] + self.TABLE_HEADINGS_GEN[_type](_process)
        return partial(
            FixedColumnTable,
            1,
            len(headings),
            2,
            pad=0,
            values=self.TABLE_VALUES[_type],
            headings=headings,
            expand_x=True, expand_y=True,
            select_mode=sg.TABLE_SELECT_MODE_NONE,
            enable_click_events=True,
        )
    def _create_tables(self):
        return {
            k: self._get_table(k) for k in ['cost', 'capacity', 'existing_capacity']
        }

    def _show_table(self, process_id, table_type, window):
        if self._current_key is not None:
            self.TABLE_VALUES[self._current_key] = self._current_table.values

        headings = self.TABLE_HEADINGS_GEN[table_type](process_id)
        values = self.TABLE_VALUES[table_type]
        self._current_key = table_type
        self._current_table = FixedColumnTable(
            1,
            len(headings),
            2,
            pad=0,
            values=values,
            headings=headings,
            expand_x=True, expand_y=True,
            select_mode=sg.TABLE_SELECT_MODE_NONE,
            enable_click_events=True,
        )

