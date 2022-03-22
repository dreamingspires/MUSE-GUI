from functools import partial
from typing import Optional, Dict, List
import PySimpleGUI as sg
from PySimpleGUI import Element
from .base import BaseWidget


class TabGroup(BaseWidget):
    def __init__(self,  tabs: Dict[str, BaseWidget], key: Optional[str] = None):
        super().__init__(key)
        self._tabs = tabs
        self._tg = partial(
            sg.TabGroup,
            enable_events=True,
            expand_x=True, expand_y=True,
        )

    def layout(self, prefix) -> List[List[Element]]:
        if not self._layout:
            self.prefix = prefix
            self._tg = self._tg(
                [[sg.Tab(k.title(), tab.layout(self._prefixf()))] for k, tab in self._tabs.items()],
                key=self._prefixf()
            )

            self._layout = [[
                self._tg
            ]]
        return self._layout

    def bind_handlers(self):
        for _tab in self._tabs.values():
            _tab.bind_handlers()

    def __call__(self, window, event, values):
        print('Tab group received - ', event)
        if event == self._prefixf():
            # Tab switch event
            current_tab = self._tabs[self._tg.get().lower()]
            current_tab.update(window)
        else:
            for _tab in self._tabs.values():
                if _tab.should_handle_event(event):
                    return _tab(window, event, values)


