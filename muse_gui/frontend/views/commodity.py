from functools import partial
from typing import List
import PySimpleGUI as sg
from PySimpleGUI import Element

from ...backend.resources.datastore import Datastore
from ...backend.data.commodity import Commodity

from ..widgets.listbox import ListboxWithButtons
from ..widgets.table import FixedColumnTable
from ..widgets.form import Form
from .base import TwoColumnMixin, BaseView


class CommodityView(TwoColumnMixin, BaseView):
    def __init__(self, model: Datastore):
        super().__init__('commodity')
        self._parent_model = model
        self.model = model.commodity
        self._commodity_list = partial(
            ListboxWithButtons
        )
        self._commodity_info = partial(
            Form,
            Commodity
        )
        self._prices_table = partial(
            FixedColumnTable,
            1,
            3,
            2,
            pad=0,
            values=[[0, 0, 0]],
            headings=['Year', 'Region', 'Price'],
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

    def update(self, window):
        _commodities = self.model.list()
        self._commodity_list.update(_commodities)
        self.selected = min(self.selected, len(_commodities) - 1)
        self._commodity_list.indices = [self.selected] if self.selected != -1 else None
        if self.selected != -1:
            _commodity_info = self.model.read(_commodities[self.selected])
            self._commodity_info.update(window, _commodity_info)
            _prices = _commodity_info.commodity_prices
            _values = [[p.time, p.region_name, p.value] for p in _prices]
            self._prices_table.values = _values

    def layout(self, prefix) -> List[List[Element]]:
        if not self._layout:
            self.prefix = prefix

            self._commodity_list = self._commodity_list()
            self._commodity_info = self._commodity_info()

            # Left Column
            self.column_1 = sg.Col(
                self._commodity_list.layout(self._prefixf()),
                expand_y=True
            )

            _commodity_info_layout = self._commodity_info.layout(
                self._prefixf(),
                [
                    ['commodity'],
                    ['commodity_type'],
                    ['c_emission_factor_co2'],
                    ['heat_rate'],
                    ['unit']
                ]
            )
            self._prices_table = self._prices_table()
            _prices_layout = [
                [],
                [
                    sg.Text('Price Projection', auto_size_text=True), sg.HorizontalSeparator()
                ],
                [sg.Button('Add Year'), sg.Button('Zero All')],

            ] + self._prices_table.layout(self._prefixf('prices') )

            self.column_2 = sg.Column(
                _commodity_info_layout + _prices_layout,
                expand_x=True,expand_y=True)

            self._layout = [
                [self.column_1, self.column_2],
            ]
        return self._layout

    def bind_handlers(self):
        self._prices_table.bind_handlers()


    def __call__(self, window, event, values):
        print('Commodity view handling - ', event)
        address = event
        if event[0] and isinstance(event[0], tuple):
            address = event[0]

        _event = address[len(self._prefixf()):][0]

        if _event == 'listbox':
            # Selection event
            indices = self._commodity_list.indices
            if len(indices):
                self.selected = indices[0]
                self.update(window)

        elif _event == 'prices':
            self._prices_table(window, event, values)

        pass
