from typing import Dict
from pydantic import BaseModel
from PySimpleGUI.PySimpleGUI import Element


class Data(BaseModel):
    def item(self) -> Dict[str, Element]:
        raise NotImplementedError

    @classmethod
    def heading(cls) -> Dict[str, Element]:
        raise NotImplementedError
