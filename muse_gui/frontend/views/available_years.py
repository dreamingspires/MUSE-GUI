from functools import partial
from typing import List
import PySimpleGUI as sg
from PySimpleGUI import Element
from math import inf

from ...backend.resources.datastore import Datastore
from ...backend.resources.datastore.exceptions import KeyAlreadyExists
from ...backend.data.timeslice import AvailableYear

from ..widgets.listbox import ListboxWithButtons
from .base import BaseView, TwoColumnMixin


class AvailableYearsView(TwoColumnMixin, BaseView):
    def __init__(self, model: Datastore):
        super().__init__('available_years')
        self._parent_model = model
        self.model = model.available_year
        self._year_list_maker = partial(
            ListboxWithButtons
        )
        self._selected = -1

    @property
    def selected(self):
        return self._selected
    @selected.setter
    def selected(self, v):
        if self._selected == v:
            return
        self._selected = v

    def update(self, _=None):
        _years = self.model.list()
        self.selected = min(self.selected, len(_years) - 1)
        self._year_list.update(_years)
        self._year_list.indices = [self.selected] if self.selected != -1 else None

    def layout(self, prefix) -> List[List[Element]]:
        if not self._layout:
            self.prefix = prefix
            # Left column
            self._year_list = self._year_list_maker()

            # Right Column
            _help = (
                'Tip:\n'
                '\n'
                'Add new years by using the "Add" button.\n'
                '\n'
            )
            _right = [
                [sg.Multiline(
                    _help,
                    size=(25, 12),
                    expand_x=True,
                    disabled=True,
                    write_only=True,
                    no_scrollbar=True,
                )],
            ]
            self.column_1 = sg.Column(
                self._year_list.layout(self._prefixf()),
                expand_y=True
            )
            self.column_2 = sg.Column(
                _right,
                expand_x=True, expand_y=True
            )
            self._layout = [
                [self.column_1, self.column_2]
            ]
        return self._layout

    def bind_handlers(self):
        pass

    def __call__(self, window, event, values):
        print('Region view handling - ', event)

        address = event
        if event[0] and isinstance(event[0], tuple):
            address = event[0]

        _event = address[len(self._prefixf()):][0]

        if _event == 'listbox':
            # Selection event
            indices = self._year_list.indices
            if len(indices):
                self.selected = indices[0]

        elif _event == 'add':
            # Add event
            # Show pop up and add years to datastore
            return self._handle_add_years()

        elif _event == 'delete':
            # Delete event
            # Show popup with dependents and confirm delete
            return self._handle_delete_years()
        else:
            # Pass it down?
            pass

    def _handle_delete_years(self):
        selected_years = self._year_list.selected

        for y in selected_years:
            self.model.delete(y)

        self.selected = max(0, self.selected - 1)
        self.update()
        return None, f'{len(selected_years)} year(s) deleted'

    def _handle_add_years(self):
        years = sg.popup_get_text(
            'Please enter year(s) to add, seperated by commas', 'Add Simulation Year(s)')
        if years == None or years.strip() == '':
            return None, '0 years added'
        try:
            counter = 0
            for x in years.split(','):
                try:
                    self.model.create(AvailableYear(year=x.strip()))
                    counter += 1
                except KeyAlreadyExists as e:
                    pass

            self.selected = inf
            self.update()
            return None, f'{counter} year(s) added'

        except Exception as e:
            return e, 'Add Year(s) failed!'
