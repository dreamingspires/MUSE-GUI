from functools import partial
from typing import List
import PySimpleGUI as sg
from PySimpleGUI import Element
from math import inf

from ...backend.resources.datastore import Datastore


from ...backend.resources.datastore.exceptions import KeyAlreadyExists
from ...backend.data.region import Region

from ..widgets.listbox import ListboxWithButtons
from .base import BaseView, TwoColumnMixin


class RegionView(TwoColumnMixin, BaseView):

    def __init__(self, model: Datastore):
        super().__init__('region')
        self._parent_model = model
        self.model = model.region
        self._region_list = partial(
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
        _regions = self.model.list()
        self.selected = min(self.selected, len(_regions) - 1)
        self._region_list.update(_regions)
        self._region_list.indices = [self.selected] if self.selected != -1 else None

    def layout(self, prefix) -> List[List[Element]]:
        if not self._layout:
            self.prefix = prefix
            # Left column
            self._region_list = self._region_list()

            # Right Column
            _help = (
                'Tip:\n'
                '\n'
                'Add new regions by using the "Add" button.\n'
                '\n'
                'Delete region(s) by selecting them and deleting it.\n'
                '\n'
                'Edit region by selecting a row and clicking "Edit"'
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
                self._region_list.layout(self._prefixf()),
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
            indices = self._region_list.indices
            if len(indices):
                self.selected = indices[0]

        elif _event == 'add':
            # Add event
            # Show pop up and add regions to datastore
            return self._handle_add_regions()

        elif _event == 'delete':
            # Delete event
            # Show popup with dependents and confirm delete
            return self._handle_delete_regions()
        else:
            # Pass it down?
            pass

    def _handle_delete_regions(self):
        selected_regions = self._region_list.selected

        for r in selected_regions:
            self.model.delete(r)

        self.selected = max(0, self.selected - 1)
        self.update()
        return None, f'{len(selected_regions)} region(s) deleted'

    def _handle_add_regions(self):
        regions = sg.popup_get_text(
            'Please enter region(s) to add, seperated by commas', 'Add Region(s)')
        if regions == None or regions.strip() == '':
            return None, '0 regions added'
        try:
            counter = 0
            for x in regions.split(','):
                try:
                    self.model.create(Region(name=x.strip()))
                    counter += 1
                except KeyAlreadyExists as e:
                    pass

            self.selected = inf
            self.update()
            return None, f'{counter} region(s) added'

        except Exception as e:
            return e, 'Add region(s) failed!'
