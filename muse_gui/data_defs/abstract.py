from typing import Dict
from pydantic import BaseModel

from PySimpleGUI.PySimpleGUI import Element


from pydantic.main import BaseModel

class Data(BaseModel):
    def item(self) -> Dict[str,Element]:
        raise NotImplementedError
    @classmethod
    def heading(cls) -> Dict[str, Element]:
        raise NotImplementedError
