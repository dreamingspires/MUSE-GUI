from functools import partial
from typing import Optional, List
import PySimpleGUI as sg
from PySimpleGUI import Element
from .base import BaseWidget


class ListboxWithButtons(BaseWidget):
    def __init__(self, key: Optional[str] = None, **kwargs):
        super().__init__(key)

        values = kwargs.pop('values', [])
        expand_x = kwargs.pop('expand_x', True)
        expand_y = kwargs.pop('expand_y', True)
        size = kwargs.pop('size', kwargs.pop('s', (25, 10)))
        enable_events = kwargs.pop('enable_events', True)

        self._listbox = partial(
            sg.Listbox,
            values,
            size=size,
            expand_x=expand_x,
            expand_y=expand_y,
            enable_events=enable_events,
            **kwargs,
        )

    @property
    def selected(self):
        return self._listbox.get()

    @property
    def indices(self):
        return self._listbox.get_indexes()

    @property
    def values(self):
        return self._listbox.get_list_values()

    @values.setter
    def values(self, values):
        self._listbox.update(values=values)

    @indices.setter
    def indices(self, indices):
        self._listbox.update(set_to_index=indices)

    def update(self, values):
        self.values = values

    def bind_handlers(self):
        pass

    def layout(self, prefix) -> List[List[Element]]:
        if not self._layout:
            self.prefix = prefix
            self._listbox = self._listbox(
                key=self._prefixf('listbox')
            )
            self._layout = [
                [
                    self._listbox
                ],
                [
                    sg.Push(),
                    sg.Button('Add', key=self._prefixf('add')),
                    sg.Button('Delete', key=self._prefixf('delete')),
                ]
            ]
        return self._layout
