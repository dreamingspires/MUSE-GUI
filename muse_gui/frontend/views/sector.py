from functools import partial
from typing import List
import PySimpleGUI as sg
from PySimpleGUI import Element
from ...backend.data.sector import BaseSector
from ...backend.resources.datastore import Datastore
from ..widgets.listbox import ListboxWithButtons
from ..widgets.form import Form
from .base import BaseView, TwoColumnMixin


class SectorView(TwoColumnMixin, BaseView):
    def __init__(self, model: Datastore):
        super().__init__('sector')
        self._parent_model = model
        self.model = model.sector
        self._sector_list_maker = partial(
            ListboxWithButtons
        )
        self._sector_info_maker = partial(
            Form,
            BaseSector
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
        _sectors = self.model.list()
        self._sector_list.update(_sectors)
        self.selected = min(self.selected, len(_sectors) - 1)
        self._sector_list.indices = [self.selected] if self.selected != -1 else None

        if self.selected != -1:
            _sector_info = self.model.read(_sectors[self.selected])
            self._sector_info.update(window, _sector_info)

    def layout(self, prefix) -> List[List[Element]]:
        if not self._layout:
            self.prefix = prefix

            self._sector_list = self._sector_list_maker()
            self._sector_info = self._sector_info_maker()

            # Left Column
            self.column_1 = sg.Col(
                self._sector_list.layout(self._prefixf()),
                expand_y=True
            )

            _sector_info_layout = self._sector_info.layout(
                self._prefixf(),
                [
                    ['name'],
                    ['priority'],
                    ['type'],
                ]
            )

            self.column_2 = sg.Col(
                #_sector_info_layout + [[self._default]],
                _sector_info_layout,
                expand_y=True, expand_x=True)

            self._layout = [
                [self.column_1, self.column_2],
            ]
        return self._layout

    def bind_handlers(self):
        pass

    def __call__(self, window, event, values):
        print('Sector view handling - ', event)
        address = event
        if event[0] and isinstance(event[0], tuple):
            address = event[0]

        _event = address[len(self._prefixf()):][0]

        if _event == 'listbox':
            # Selection event
            indices = self._sector_list.indices
            if len(indices):
                self.selected = indices[0]
                self.update(window)

        pass
