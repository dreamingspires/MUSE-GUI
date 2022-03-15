from typing import Dict

from pydantic import BaseModel
from .abstract import Data, View
import PySimpleGUI as sg
from PySimpleGUI import Element


class Region(Data):
    name: str


class RegionView(View):
    model: Region

    def item(self) -> Dict[str, Element]:
        return {
            'name': sg.Input(self.model.name),
        }

    @classmethod
    def heading(cls) -> Dict[str, Element]:
        return {
            k: sg.Text(k.title()) for k in Region.__fields__.keys()
        }
