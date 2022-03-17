from typing import Dict, List, Union
from dataclasses import dataclass
from copy import copy
Timeslice = Dict[str, Union["Timeslice", float]]
OriginalTimeslice = Dict[str, Union[Timeslice, float, List[str]]]
@dataclass
class TimesliceInfo:
    timeslices: Dict[str, float]
    level_names: List[str]

def unpack_timeslice(timeslices: OriginalTimeslice) -> TimesliceInfo:
    timeslices_copy = copy(timeslices)
    def unpack_timeslice_inner(timeslice_dict: Timeslice) -> Dict[str, float]:
        new_dict = {}
        for k, v in timeslice_dict.items():
            if isinstance(v, float) or isinstance(v, int):
                new_dict[k] = v
            elif isinstance(v, dict):
                dict_of_keys = unpack_timeslice_inner(v)
                for a, b in dict_of_keys.items():
                    new_dict[k+'.'+a] = b
            else:
                raise TypeError(f'Other type {v} detected')
        return new_dict
    level_names = timeslices_copy.pop('level_names')
    if not isinstance(level_names, list):
        raise TypeError(f'Level names {level_names} is not list')
    fresh_timeslices = {}
    for k, v in timeslices_copy.items():
        if isinstance(v, list):
            raise TypeError(f'List {v} still present in timeslices')
        else:
            fresh_timeslices[k] = v
    new_timeslices = unpack_timeslice_inner(fresh_timeslices)
    return TimesliceInfo(new_timeslices, level_names)

def pack_timeslice(timeslices: TimesliceInfo) -> Timeslice:
    raise NotImplementedError
