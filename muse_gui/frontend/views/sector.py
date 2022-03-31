import random
import string
from functools import partial
from math import inf
from typing import List

import PySimpleGUI as sg
from pydantic import parse_obj_as
from PySimpleGUI import Element

from muse_gui.backend.resources.datastore.exceptions import KeyAlreadyExists
from muse_gui.frontend.views.exceptions import SaveException
from muse_gui.frontend.widgets.button import SaveEditButtons

from ...backend.data.sector import BaseSector, Sector, StandardSector
from ...backend.resources.datastore import Datastore
from ..widgets.form import Form
from ..widgets.listbox import ListboxWithButtons
from .base import BaseView, TwoColumnMixin


def get_random_string(_len=6):
    return "".join(random.choices(string.ascii_lowercase + string.digits, k=_len))


class SectorView(TwoColumnMixin, BaseView):
    def __init__(self, model: Datastore):
        super().__init__("sector")
        self._parent_model = model
        self.model = model.sector
        self._sector_list_maker = partial(ListboxWithButtons)
        self._sector_info_maker = partial(Form, BaseSector)
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

    def _update_info(self, window, model: BaseSector):
        self._sector_info.update(window, model)

    def update(self, window):
        # Ensure disabled flag and elements are in sync
        if self._editing == None:
            self.disable_editing(window, force=True)

        # Update sector list
        _sectors = self.model.list()
        _sector_names = [self.model.read(x).name for x in _sectors]
        self._update_list(_sector_names)

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
                self._sector_list.layout(self._prefixf()), expand_y=True
            )
            _button_layout = self._save_edit_btns.layout(self._prefixf())

            _sector_info_layout = self._sector_info.layout(
                self._prefixf(),
                [
                    ["name"],
                    ["priority"],
                    ["type"],
                ],
            )

            self.column_2 = sg.Col(
                _button_layout
                + [
                    [
                        sg.HorizontalSeparator(),
                    ]
                ]
                + _sector_info_layout,
                expand_y=True,
                expand_x=True,
            )

            self._layout = [
                [self.column_1, self.column_2],
            ]
        return self._layout

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

    def _handle_save(self, window, values):
        # Commit to datastore

        # Get current values from view
        _values = self._sector_info.read(values)

        # Get name in the form
        new_name = _values["name"]

        # Check if it is add mode / edit mode
        _sector_ids = self.model.list()

        if self.selected == len(_sector_ids):
            # Add mode
            try:
                sector = parse_obj_as(Sector, _values)
                self.model.create(sector)
            except KeyAlreadyExists:
                raise SaveException(f'Sector with name "{new_name}" already exists!')
            except Exception as e:
                raise SaveException() from e
        else:
            # Update mode
            # Get current model key
            _sector_id = _sector_ids[self.selected]
            _sector = self.model.read(_sector_id)

            if new_name != _sector.name:
                deps = self.model.forward_dependents(_sector)
                for d in deps:
                    if len(deps[d]):
                        # Not supporting name change for ones with forward deps
                        raise SaveException() from RuntimeError(
                            "Changing name is not supported for sectors already associated with resources"
                        )

            _model_dict = _sector.dict()
            _model_dict.update(_values)
            try:
                sector = parse_obj_as(Sector, _model_dict)
                self.model.update(_sector_id, sector)
                # Fingers crossed
            except Exception as e:
                raise SaveException() from e

        # Disable save, enable edit
        self._save_edit_btns.state = "idle"
        self.disable_editing(window)

        self.update(window)
        # Communicate save mode to parent
        return "idle", self.key

    def _handle_add_sector(self, window):
        # Create a standard sector
        sector_name = sg.popup_get_text(
            "Please enter name of sector to add",
            "Add Sector",
            "New Sector 1",
        )
        if sector_name == None or sector_name.strip() == "":
            return None, "0 sectors added"

        # Create a dummy sector with given name
        # and update view
        sector_name = sector_name.strip()
        _sector = StandardSector(name=sector_name)

        _sector_ids = self.model.list()
        _sector_names = [self.model.read(x).name for x in _sector_ids]

        _sector_names.append(sector_name)
        self.selected = inf
        self._update_list(_sector_names)
        self._update_info(window, _sector)

        # Simulate edit mode
        return self._handle_edit(window)

    def _handle_delete_sector_safe(self, sector):
        """
        Internal function that deletes the sector
        returns True / False based on whether sector was deleted or not
        """
        _sector = self.model.read(sector)
        # Compute forward dependencies
        deps = self.model.forward_dependents_recursive(_sector)

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
                f"Deleting region {_sector.name} will result in the following being deleted:\n",
                f"{dep_string}" f"Delete anyway?\n",
                title="Warning!",
            )
            if ret and ret == "Yes":
                self.model.delete(sector)
                return True
            else:
                return False
        else:
            self.model.delete(sector)
            return True

    def _handle_delete_sector(self, window):
        if self.selected == -1:
            return None, "Select a sector before attempting to delete!"

        selected_sectors = self.model.list()[self.selected]

        is_deleted = self._handle_delete_sector_safe(selected_sectors)

        if is_deleted:
            self._selected = max(0, self._selected - 1)
            self.update(window)
        return None, f'Sector "{selected_sectors}" deleted'

    def bind_handlers(self):
        pass

    def __call__(self, window, event, values):
        print("Sector view handling - ", event)
        address = event
        if event[0] and isinstance(event[0], tuple):
            address = event[0]

        _event = address[len(self._prefixf()) :][0]

        if _event == "listbox":
            # Selection event
            indices = self._sector_list.indices
            if len(indices):
                self.selected = indices[-1]
                self.update(window)

        elif _event == "add":
            # Add sector
            return self._handle_add_sector(window)

        elif _event == "delete":
            # Delete sector
            return self._handle_delete_sector(window)

        elif _event == "edit":
            # Edit event
            return self._handle_edit(window)

        elif _event == "save":
            # Save event - Commit to datastore / throw
            return self._handle_save(window, values)
        else:
            print("Unhandled event - ", event)

        return None
