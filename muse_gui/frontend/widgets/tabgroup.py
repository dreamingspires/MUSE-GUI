from functools import partial
from typing import Dict, List, Optional

import PySimpleGUI as sg
from PySimpleGUI import Element

from .base import BaseWidget


class TabGroup(BaseWidget):
    def __init__(self, tabs: Dict[str, BaseWidget], key: Optional[str] = None):
        super().__init__(key)
        self._tabs = tabs
        self._tab_group_maker = partial(
            sg.TabGroup,
            enable_events=True,
            expand_x=True,
            expand_y=True,
        )

    def enable(self, window):
        for k in self._tabs:
            _tab_key = self._tab_group.find_key_from_tab_name(k.title())
            window[_tab_key](disabled=False)

    def disable(self, window, *, exclude=[]):

        _tabs = [
            self._tab_group.find_key_from_tab_name(k.title())
            for k in self._tabs
            if k.title() not in exclude
        ]

        for _tab in _tabs:
            window[_tab](disabled=True)

    def layout(self, prefix) -> List[List[Element]]:
        if not self._layout:
            self.prefix = prefix
            self._tab_group = self._tab_group_maker(
                [
                    [sg.Tab(k.title(), tab.layout(self._prefixf()))]
                    for k, tab in self._tabs.items()
                ],
                key=self._prefixf(),
            )

            self._layout = [[self._tab_group]]
        return self._layout

    def bind_handlers(self):
        for _tab in self._tabs.values():
            _tab.bind_handlers()

    def __call__(self, window, event, values):
        print("Tab group received - ", event)
        if event == self._prefixf():
            # Possibly tab switch event
            current_tab_key = self._tab_group.get()
            if not current_tab_key:
                return
            current_tab = self._tabs[current_tab_key.lower()]
            current_tab.update(window)
        else:
            for _tab in self._tabs.values():
                if _tab.should_handle_event(event):
                    ret = _tab(window, event, values)
                    if not ret:
                        return ret

                    _ret, _ = ret
                    if _ret == "edit":
                        # Disable all tabs except this one
                        current_tab_key = self._tab_group.get()
                        self.disable(window, exclude=[current_tab_key])

                        return None, "Edit & Press save to proceed"
                    elif _ret == "idle":
                        # Enable all tabs
                        self.enable(window)
                        return None, "Ready!"
                    else:
                        return ret
