from functools import partial
from typing import List, Union

import PySimpleGUI as sg
from PySimpleGUI import Element

from muse_gui.backend.data.timeslice import LevelName, Timeslice
from muse_gui.frontend.views.exceptions import SaveException
from muse_gui.frontend.widgets.button import SaveEditButtons

from ...backend.resources.datastore import Datastore
from ..widgets.table import EditableTable
from .base import BaseView


class TimesliceModelHelper:
    def __init__(self, model: Datastore):
        self._model = model
        self._lmodel = model.level_name
        self._tmodel = model.timeslice

    @property
    def levelnames_list(self):
        return self._lmodel.list()

    @property
    def timeslices_list(self):
        return self._tmodel.list()

    @property
    def timeslices(self):
        return [self._tmodel.read(x) for x in self.timeslices_list]

    @property
    def levelnames(self):
        return [self._lmodel.read(x) for x in self.levelnames_list]

    @levelnames.setter
    def levelnames(self, val: List[Union[LevelName, str]]):
        self.delete_all_levelnames()
        for v in val:
            self._lmodel.create(v if isinstance(v, LevelName) else LevelName(level=v))

    @timeslices.setter
    def timeslices(self, val: List[Union[Timeslice, List]]):
        self.delete_all_timeslices()
        for v in val:
            self._tmodel.create(
                v if isinstance(v, Timeslice) else Timeslice(name=v[0], value=v[1])
            )

    def replace_all(self, level_names: List[str], timeslices: List[List]):
        # Save
        _current_level_names = self.levelnames
        _current_timeslices = self.timeslices

        try:
            self.levelnames = level_names
            self.timeslices = timeslices
        except Exception as e:
            self.levelnames = _current_level_names
            self.timeslices = _current_timeslices
            raise e

    def delete_all_levelnames(self):
        for x in self.levelnames_list:
            self._lmodel.delete(x)

    def delete_all_timeslices(self):
        for x in self.timeslices_list:
            self._tmodel.delete(x)


class TimesliceView(BaseView):
    def __init__(self, model: Datastore):
        super().__init__("timeslice")
        self.model = TimesliceModelHelper(model)
        self._timeslice_maker = partial(
            EditableTable,
            0,
            2,
            pad=0,
            values=[[]],
            headings=["Level", "Weight"],
            expand_x=True,
            expand_y=True,
            select_mode=sg.TABLE_SELECT_MODE_NONE,
            enable_click_events=True,
        )
        self._level_names_maker = partial(
            sg.Input,
            size=(30, 1),
        )
        self._save_edit_btns = SaveEditButtons()

        self._disabled = True

    @property
    def disabled(self):
        return self._disabled

    @disabled.setter
    def disabled(self, val: bool):
        self._timeslice.disabled = val
        self._level_names.update(disabled=val)
        self._disabled = val

    def _update_level_name(self):
        self._level_names.update(",".join([x.level for x in self.model.levelnames]))

    def _update_timeslices(self):
        self._timeslice.values = [[x.name, x.value] for x in self.model.timeslices]

    def update(self, window=None):
        # Update level names
        self._update_level_name()

        # Update timeslice table
        self._update_timeslices()

    def layout(self, prefix) -> List[List[Element]]:
        if not self._layout:
            self.prefix = prefix
            self._timeslice = self._timeslice_maker()
            self._level_names = self._level_names_maker(key=self._prefixf("level_name"))

            # Layout buttons
            _button_layout = self._save_edit_btns.layout(self._prefixf())

            # Framed table + level name input
            _level_name_layout = [
                [
                    sg.Text("Level Names", size=(10, 1)),
                    sg.Text(":", auto_size_text=True),
                    self._level_names,
                ],
                [
                    sg.Text(""),
                ],
            ]
            _timeslice_layout = self._timeslice.layout(self._prefixf("timeslice"))
            _left_frame = sg.Frame(
                "",
                _level_name_layout + _timeslice_layout,
                expand_x=True,
                expand_y=True,
            )
            _left = _button_layout + [[_left_frame]]

            # Right Column
            _help = (
                "Docs: \n"
                "\n"
                "https://museenergydocs.readthedocs.io/en/latest/inputs/toml.html#timeslices"
            )
            _right = [
                [
                    sg.Multiline(
                        _help,
                        size=(35, 12),
                        expand_x=True,
                        disabled=True,
                        write_only=True,
                        no_scrollbar=True,
                    )
                ],
            ]
            self.column_1 = sg.Column(
                _left,
                expand_y=True,
                expand_x=True,
            )
            self.column_2 = sg.Column(_right, expand_x=True, expand_y=True)
            self._layout = [[self.column_1, self.column_2]]
        return self._layout

    def bind_handlers(self):
        self.disabled = True
        self._timeslice.bind_handlers()

    def _handle_edit(self):
        if self.disabled == False:
            # Already in edit state, so reset
            self._save_edit_btns.state = "idle"
            self.disabled = True
            self.update()
            return "idle", self.key

        # Disable edit, enable save
        self._save_edit_btns.state = "edit"

        # Enable table and level names
        self.disabled = False

        # Communicate edit mode to parent
        return "edit", self.key

    def _handle_save(self):
        # Commit to datastore
        _lname = self._level_names.get()
        if not _lname:
            self._update_level_name()
            raise SaveException(
                "Update level names failed - Level names cannot be empty!"
            )

        _current_level_names = []
        for l in _lname.split(","):
            l = l.strip()
            if not l:
                continue
            _current_level_names.append(l)

        if not len(_current_level_names):
            self._update_level_name()
            raise SaveException(
                "Update level names failed - Level names cannot be empty!"
            )

        try:
            self.model.replace_all(_current_level_names, self._timeslice.values)
        except Exception as e:
            raise SaveException() from e

            # Fingers crossed

        # Disable save, enable edit
        self._save_edit_btns.state = "idle"
        self.disabled = True

        self.update()
        # Communicate save mode to parent
        return "idle", self.key

    def __call__(self, window, event, values):
        print("Timeslice view handling - ", event)

        address = event
        if event[0] and isinstance(event[0], tuple):
            address = event[0]

        _event = address[len(self._prefixf()) :][0]

        if _event == "edit":
            return self._handle_edit()

        if _event == "save":
            return self._handle_save()

        if _event == "timeslice":
            self._timeslice(window, event, values)
