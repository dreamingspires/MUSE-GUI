from functools import partial
from typing import List, Optional

import PySimpleGUI as sg
from PySimpleGUI import Element

from muse_gui.frontend.widgets.button import AddDeleteButtons, DoneCancelButtons
from muse_gui.frontend.widgets.utils import get_btn_maker

from .base import BaseWidget


class Listbox(BaseWidget):
    def __init__(self, key: Optional[str] = None, **kwargs):
        super().__init__(key)

        values = kwargs.pop("values", [])
        expand_x = kwargs.pop("expand_x", True)
        expand_y = kwargs.pop("expand_y", True)
        size = kwargs.pop("size", kwargs.pop("s", (25, 10)))
        enable_events = kwargs.pop("enable_events", True)

        self._listbox_maker = partial(
            sg.Listbox,
            values,
            size=size,
            expand_x=expand_x,
            expand_y=expand_y,
            enable_events=enable_events,
            **kwargs,
        )
        self._disabled = False

    @property
    def disabled(self):
        return self._disabled

    @disabled.setter
    def disabled(self, val: bool):
        if self._disabled == val:
            return
        self._listbox.update(disabled=val)
        self._disabled = val

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

    def layout(self, prefix):
        if not self._layout:
            self.prefix = prefix
            self._listbox = self._listbox_maker(key=self._prefixf("listbox"))
            self._layout = [[self._listbox]]
        return self._layout


class ListboxWithButtons(Listbox):
    def __init__(self, key: Optional[str] = None, values=[]):
        super().__init__(key, values=values)
        self._btns = AddDeleteButtons()

        self._disabled = False

    @property
    def disabled(self):
        return self._disabled

    @disabled.setter
    def disabled(self, val: bool):
        if self._disabled == val:
            return
        self._listbox.update(disabled=val)
        self._btns.disabled = val
        self._disabled = val

    def layout(self, prefix) -> List[List[Element]]:
        if not self._layout:
            self.prefix = prefix
            _listbox_layout = super().layout(prefix=self._prefixf())
            _btn_layout = self._btns.layout(self._prefixf())
            self._layout = _listbox_layout + _btn_layout
        return self._layout


class DualListbox(BaseWidget):
    def __init__(self, key: Optional[str] = None, values1=[], values2=[]):
        super().__init__(key)

        self._listbox1 = Listbox(values=values1)
        self._listbox2 = Listbox(values=values2)
        self._btns = DoneCancelButtons()

        self._addremovebuttons = {
            k[0]: get_btn_maker(k[1], size=(4, 2), pad=(8, 4))
            for k in [
                ("remove_all", "<<"),
                ("remove", "<"),
                ("add", ">"),
                ("add_all", ">>"),
            ]
        }

    def layout(self, prefix) -> List[List[Element]]:
        if not self._layout:
            self.prefix = prefix
            _addremove_col = sg.Col(
                [[sg.VPush()]]
                + [[v(key=self._prefixf(k))] for k, v in self._addremovebuttons.items()]
                + [[sg.VPush()]],
                expand_y=True,
            )

            _l1 = self._listbox1.layout(prefix=self._prefixf("l1"))[0][0]
            _l2 = self._listbox2.layout(prefix=self._prefixf("l2"))[0][0]
            _layout = [
                [_l1, _addremove_col, _l2],
            ] + self._btns.layout(self._prefixf())

            self._layout = _layout
        return self._layout

    def bind_handlers(self):
        pass

    def _handle_transfer(self, _from, _to):
        _selected = _from.selected
        if len(_selected) == 0:
            return

        _old_values = _to.values
        _lidx = len(_old_values)

        _to.values += _selected
        _to.indices = [_lidx + i for i in range(len(_selected))]

        _from.values = [x for x in _from.values if x not in _selected]
        _from.indices = []

    def _handle_transfer_all(self, _from, _to):
        _values = _from.values
        if len(_values) == 0:
            return

        _old_values = _to.values
        _lidx = len(_old_values)
        _to.values += _values
        _to.indices = [_lidx + i for i in range(len(_values))]

        _from.values = []
        _from.indices = []

    def _handle_add(self):
        self._handle_transfer(self._listbox1, self._listbox2)

    def _handle_remove(self):
        self._handle_transfer(self._listbox2, self._listbox1)

    def _handle_add_all(self):
        self._handle_transfer_all(self._listbox1, self._listbox2)

    def _handle_remove_all(self):
        self._handle_transfer_all(self._listbox2, self._listbox1)

    def __call__(self, window, event, values):
        print("Dual listbox view handling - ", event)
        address = event
        if event[0] and isinstance(event[0], tuple):
            address = event[0]

        _event = address[len(self._prefixf()) :][0]

        if _event == "l1":
            # Listbox selection event
            if len(self._listbox2.indices):
                self._listbox2.indices = []
            return

        elif _event == "l2":
            # Listbox selection event
            if len(self._listbox1.indices):
                self._listbox1.indices = []
            return

        elif _event == "add":
            # Add event
            return self._handle_add()

        elif _event == "add_all":
            # Add all event
            return self._handle_add_all()

        elif _event == "remove":
            return self._handle_remove()

        elif _event == "remove_all":
            return self._handle_remove_all()

        elif _event == "done":
            return "done", (self._listbox1.values, self._listbox2.values)

        elif _event == "cancel":
            return "cancel", None

        else:
            print("Unhandled event - ", event)

        return None
