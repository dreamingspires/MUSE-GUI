from abc import abstractmethod
from typing import Optional

import PySimpleGUI as sg

from ..widgets.base import BaseWidget


class BaseView(BaseWidget):
    def __init__(self, key: Optional[str] = None):
        super().__init__(key)

    @abstractmethod
    def update(self, window=None):
        raise NotImplementedError()


class TwoColumnMixin:
    column_1: sg.Col
    column_2: sg.Col

    def pack(self):
        column_1_widget = self.column_1.Widget
        column_2_widget = self.column_2.Widget

        info = column_1_widget.pack_info()
        info.update({"expand": 0})
        column_1_widget.pack(**info, before=column_2_widget)
