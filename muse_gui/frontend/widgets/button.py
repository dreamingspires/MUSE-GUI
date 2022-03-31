from typing import List, Optional

import PySimpleGUI as sg
from PySimpleGUI import Element

from muse_gui.frontend.widgets.utils import get_btn_maker

from .base import BaseWidget


class DoneCancelButtons(BaseWidget):
    def __init__(self, key: Optional[str] = None):
        super().__init__(key)

    def layout(self, prefix):
        if not self._layout:
            self.prefix = prefix

            self._layout = [
                [
                    sg.Push(),
                    get_btn_maker("Done")(key=self._prefixf("done")),
                    get_btn_maker("Cancel")(key=self._prefixf("cancel")),
                    sg.Push(),
                ],
            ]
        return self._layout


class AddDeleteButtons(BaseWidget):
    def __init__(self, key: Optional[str] = None):
        super().__init__(key)

        self._add_disabled = False
        self._delete_disabled = False

    def disable_add(self):
        if not self._add_disabled:
            self._add_btn.update(disabled=True)
            self._add_disabled = True

    def disable_delete(self):
        if not self._delete_disabled:
            self._delete_btn.update(disabled=True)
            self._delete_disabled = True

    def enable_add(self):
        if self._add_disabled:
            self._add_btn.update(disabled=False)
            self._add_disabled = False

    def enable_delete(self):
        if self._delete_disabled:
            self._delete_btn.update(disabled=False)
            self._delete_disabled = False

    @property
    def disabled(self):
        return self._add_disabled and self._delete_disabled

    @disabled.setter
    def disabled(self, val):
        if self.disabled == val:
            return

        if val:
            self.disable_add()
            self.disable_delete()
        else:
            self.enable_add()
            self.enable_delete()

    def layout(self, prefix) -> List[List[Element]]:
        if not self._layout:
            self.prefix = prefix

            self._add_btn = get_btn_maker("Add")(key=self._prefixf("add"))
            self._delete_btn = get_btn_maker("Delete")(key=self._prefixf("delete"))

            self._layout = [
                [
                    sg.Push(),
                    self._add_btn,
                    self._delete_btn,
                ],
            ]
        return self._layout

    def bind_handlers(self):
        pass


class SaveEditButtons(BaseWidget):
    def __init__(self, key: Optional[str] = None):
        super().__init__(key)

        self._edit_btn_maker = get_btn_maker("Edit")
        self._save_btn_maker = get_btn_maker("Save", disabled=True)

        self._state = "idle"

    @property
    def state(self):
        return self._state

    @state.setter
    def state(self, val):
        if val not in ["edit", "idle"]:
            raise ValueError(f'Expected "idle" or "edit", got {val}')

        if self._state == val:
            return

        if val == "edit":
            self._edit_btn.update(text="Discard", button_color=("red", "white"))
            self._save_btn.update(disabled=False)
        else:
            self._edit_btn.update(text="Edit", button_color=sg.theme_button_color())
            self._save_btn.update(disabled=True)

        self._state = val

    def layout(self, prefix) -> List[List[Element]]:
        if not self._layout:
            self.prefix = prefix

            self._edit_btn = self._edit_btn_maker(key=self._prefixf("edit"))
            self._save_btn = self._save_btn_maker(key=self._prefixf("save"))

            self._layout = [
                [
                    sg.Push(),
                    self._edit_btn,
                    self._save_btn,
                ],
            ]
        return self._layout

    def bind_handlers(self):
        pass
