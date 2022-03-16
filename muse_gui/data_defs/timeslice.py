from muse_gui.data_defs.abstract import Data

class Timeslice(Data):
    name: str
    value: float

class LevelName(Data):
    level: str

class AvailableYear(Data):
    year: int
