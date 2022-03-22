from functools import partial
from typing import List
import PySimpleGUI as sg
from PySimpleGUI import Element

from ...backend.resources.datastore import Datastore

from .base import BaseView
from ..widgets.table import EditableTable

class TimesliceView(BaseView):

    def __init__(self, model: Datastore):
        super().__init__('region')
        self._parent_model = model
        self.model = model.timeslice
        self._timeslice_maker = partial(
            EditableTable,
            1,
            2,
            pad=0,
            values=[[]],
            headings=['Level', 'Weight'],
            expand_x=True, expand_y=True,
            select_mode=sg.TABLE_SELECT_MODE_NONE,
            enable_click_events=True,
        )
        self._level_names_maker = partial(
            sg.Input,
            size=(30, 1),
        )

    def update(self, window):
        # Update level names
        _levels = self._parent_model.level_name.list()
        self._level_names.update(','.join(_levels))

        # Update timeslice table
        _timeslices = self.model.list()
        _values = []
        for x in _timeslices:
            _value = self.model.read(x)
            _values.append([_value.name, _value.value])
        self._timeslice.values = _values

    def layout(self, prefix) -> List[List[Element]]:
        if not self._layout:
            self.prefix = prefix
            self._timeslice = self._timeslice_maker()
            self._level_names = self._level_names_maker(key=self._prefixf('level_name'))
            _left = [
                [
                    sg.Text('Timeslices'),
                     sg.HorizontalSeparator(),
                ]
            ]
            _left += self._timeslice.layout(self._prefixf('timeslice'))
            _left += [
                [
                    sg.Text(''),
                ],
                [
                    sg.Text('Level Names', size=(10, 1)),
                    sg.Text(':', auto_size_text=True),
                    self._level_names,
                ],
            ]
            # Right Column
            _help = (
                'Docs: \n'
                '\n'
                'https://museenergydocs.readthedocs.io/en/latest/inputs/toml.html#timeslices'
            )
            _right = [
                [sg.Multiline(
                    _help,
                    size=(35, 12),
                    expand_x=True,
                    disabled=True,
                    write_only=True,
                    no_scrollbar=True,
                )],
            ]
            self.column_1 = sg.Column(
                _left,
                expand_y=True,
                expand_x=True,
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
        self._timeslice.bind_handlers()


    def __call__(self, window, event, values):
        print('Tiemslice view handling - ', event)

        address = event
        if event[0] and isinstance(event[0], tuple):
            address = event[0]

        _event = address[len(self._prefixf()):][0]

        if _event == 'timeslice':
            self._timeslice(window, event, values)