from functools import partial
from math import inf
from typing import List
import PySimpleGUI as sg
from PySimpleGUI import Element
from pydantic import parse_obj_as

from muse_gui.frontend.widgets.button import SaveEditButtons
from ...backend.data.sector import BaseSector, Sector, StandardSector
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
        self._save_edit_btns = SaveEditButtons()

        self._editing = None
        self._selected = -1

    def enable_editing(self, window, force=False):
        # Careful, If enabled, form should be disabled
        # and vice versa
        if not self._editing or force:
            self._sector_info.enable(window)
            self._sector_list.disabled = True
            self._editing = True

    def disable_editing(self, window, force=False):
        # Careful, If disabled is true, form should be enabled
        # and vice versa
        if self._editing or force:
            self._sector_info.disable(window)
            self._sector_list.disabled = False
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


    def _update_list(self, _sectors):
        self._sector_list.update(_sectors)

        self.selected = min(self.selected, len(_sectors) - 1)
        self._sector_list.indices = [self.selected] if self.selected != -1 else None

        return _sectors

    def _update_info(self, window, model: BaseSector):
        self._sector_info.update(window, model)

    def update(self, window):
        # Ensure disabled flag and elements are in sync
        if self._editing == None:
            self.disable_editing(window, force=True)

        # Update sector list
        _sectors = self.model.list()
        self._update_list(_sectors)

        if self.selected != -1:
            _sector_info = self.model.read(_sectors[self.selected])
            self._update_info(window, _sector_info)

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
            _button_layout = self._save_edit_btns.layout(self._prefixf())

            _sector_info_layout = self._sector_info.layout(
                self._prefixf(),
                [
                    ['name'],
                    ['priority'],
                    ['type'],
                ]
            )

            self.column_2 = sg.Col(
                _button_layout + [
                    [
                        sg.HorizontalSeparator(),
                    ]
                ] + _sector_info_layout,
                expand_y=True, expand_x=True)

            self._layout = [
                [self.column_1, self.column_2],
            ]
        return self._layout

    def _handle_edit(self, window):
        if self._editing == True:
            # Already in edit state, so reset
            self.update(window)
            return 'idle', self.key

        # Disable edit, enable save
        self._save_edit_btns.state = 'edit'

        # Enable sector info, disable list
        self.enable_editing(window)

        # Communicate edit mode to parent
        return 'edit', self.key

    def _handle_save(self, window, values):
        # Commit to datastore

        # Get current model key
        _sector = self._sector_list.selected[-1]

        # Get current values from form
        _values = self._sector_info.read(values)

        new_name = _values['name']
        if new_name != _sector:
            deps = self.model.forward_dependents(self.model.read(_sector))
            for d in deps:
                if len(deps[d]):
                    # Not supporting name change for ones with forward deps
                    return RuntimeError('Changing name is not supported for sectors already associated with resources'), 'Save failed, Please fix the errors'

        _model = self.model.read(_sector).dict()
        _model.update(_values)
        try:
            sector = parse_obj_as(Sector, _model)
            self.model.update(_sector, sector)
        except Exception as e:
            return e, 'Save failed. Please fix the errors'
            # Fingers crossed

        # Disable save, enable edit
        self._save_edit_btns.state = 'idle'
        self.disable_editing(window)

        self.update(window)
        # Communicate save mode to parent
        return 'idle', self.key

    def _handle_add_sector(self, window):
        # Create a standard sector
        sector_name = sg.popup_get_text(
            'Please enter name of sector to add', 'Add Sector',
            'New Sector 1',
        )
        if sector_name == None or sector_name.strip() == '':
            return None, '0 sectors added'

        sector_name = sector_name.strip()
        self.model.create(StandardSector(name=sector_name))

        # Update view
        self.selected = inf
        self.update(window)

        # Simulate edit mode
        return self._handle_edit(window)

    def _handle_delete_region_safe(self, sector):
        '''
        Internal function that deletes the sector
        returns True / False based on whether sector was deleted or not
        '''
        # Compute forward dependencies
        deps = self.model.forward_dependents_recursive(self.model.read(sector))

        # Check if deps are empty
        empty_deps = True
        dep_string = ''
        for d in deps:
            if len(deps[d]):
                empty_deps = False
                dep_string += f'{d}:\n'
                dep_string += ','.join(deps[d])
                dep_string += '\n\n'


        # Show popup to confirm
        if not empty_deps:
            ret = sg.popup_yes_no(
                f'Deleting region {sector} will result in the following being deleted:\n',
                f'{dep_string}'
                f'Delete anyway?\n',
                title="Warning!",
            )
            if ret and ret == 'Yes':
                self.model.delete(sector)
                return True
            else:
                return False
        else:
            self.model.delete(sector)
            return True

    def _handle_delete_sector(self, window):
        selected_sectors = self._sector_list.selected
        if len(selected_sectors) == 0:
            return None, 'Select a sector before attempting to delete!'

        counter = 0
        for s in selected_sectors:
            counter += self._handle_delete_region_safe(s)

        self._selected = max(0, self._selected - counter)
        self.update(window)
        return None, f'{counter} sector(s) deleted'

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

        elif _event == 'add':
            # Add sector
            return self._handle_add_sector(window)

        elif _event == 'delete':
            # Delete sector
            return self._handle_delete_sector(window)

        elif _event == 'edit':
            # Edit event
            return self._handle_edit(window)

        elif _event == 'save':
            # Save event - Commit to datastore / throw
            return self._handle_save(window, values)
        else:
            print('Unhandled event - ', event)

        return None