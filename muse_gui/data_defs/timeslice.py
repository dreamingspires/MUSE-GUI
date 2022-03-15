from muse_gui.data_defs.abstract import Data

class Timeslice(Data):
    name: str
    value: float

class LevelName(str, Data):
    pass

class AvailableYear(int, Data):
    pass
