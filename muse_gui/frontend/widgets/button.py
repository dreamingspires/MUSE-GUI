from functools import partial
from typing import List, Optional

import PySimpleGUI as sg
from PySimpleGUI import Element

from .base import BaseWidget


class SaveEditButtons(BaseWidget):

    def __init__(self, key: Optional[str] = None):
        super().__init__(key)

        self._edit_btn_maker = partial(
            sg.Button,
            'Edit'
        )
        self._save_btn_maker = partial(
            sg.Button,
            'Save',
            disabled=True
        )

        self._state = 'idle'

    @property
    def state(self):
        return self._state

    @state.setter
    def state(self, val):
        if val not in ['edit', 'idle']:
            raise ValueError(f'Expected "idle" or "edit", got {val}')

        if self._state == val:
            return

        if val == 'edit':
            self._edit_btn.update(disabled=True)
            self._save_btn.update(disabled=False)
        else:
            self._edit_btn.update(disabled=False)
            self._save_btn.update(disabled=True)

        self._state = val

    def layout(self, prefix) -> List[List[Element]]:
        if not self._layout:
            self.prefix = prefix

            self._edit_btn = self._edit_btn_maker(key=self._prefixf('edit'))
            self._save_btn = self._save_btn_maker(key=self._prefixf('save'))

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