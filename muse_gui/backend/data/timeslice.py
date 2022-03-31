from .abstract import Data


class Timeslice(Data):
    name: str
    value: int


class LevelName(Data):
    level: str


class AvailableYear(Data):
    year: int
