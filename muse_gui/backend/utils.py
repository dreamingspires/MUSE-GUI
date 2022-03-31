from copy import copy
from dataclasses import dataclass
from typing import Dict, List, Union

Timeslice = Dict[str, Union["Timeslice", int]]
OriginalTimeslice = Dict[str, Union[Timeslice, int, List[str]]]


@dataclass
class TimesliceInfo:
    timeslices: Dict[str, int]
    level_names: List[str]


def unpack_timeslice(timeslices: OriginalTimeslice) -> TimesliceInfo:
    timeslices_copy = copy(timeslices)

    def unpack_timeslice_inner(timeslice_dict: Timeslice) -> Dict[str, int]:
        new_dict = {}
        for k, v in timeslice_dict.items():
            if isinstance(v, int):
                new_dict[k] = v
            elif isinstance(v, dict):
                dict_of_keys = unpack_timeslice_inner(v)
                for a, b in dict_of_keys.items():
                    new_dict[k + "." + a] = b
            else:
                raise TypeError(f"Other type {v} detected")
        return new_dict

    level_names = timeslices_copy.pop("level_names")
    if not isinstance(level_names, list):
        raise TypeError(f"Level names {level_names} is not list")
    fresh_timeslices = {}
    for k, v in timeslices_copy.items():
        if isinstance(v, list):
            raise TypeError(f"List {v} still present in timeslices")
        else:
            fresh_timeslices[k] = v
    new_timeslices = unpack_timeslice_inner(fresh_timeslices)
    return TimesliceInfo(new_timeslices, level_names)


def pack_timeslice(timeslices: TimesliceInfo) -> Timeslice:
    def pack_timeslice_inner(
        existing_dict: Timeslice, address: List[str], value: Union[int, int]
    ) -> Timeslice:
        current_point = address[0]
        if current_point in existing_dict:
            assert len(address) != 1
            current_value = existing_dict[current_point]
            assert isinstance(current_value, dict)
            existing_dict[current_point] = pack_timeslice_inner(
                current_value, address[1:], value
            )
        else:
            if len(address) == 1:
                existing_dict[current_point] = value
            else:
                existing_dict[current_point] = pack_timeslice_inner(
                    {}, address[1:], value
                )
        return existing_dict

    final_dict = {}
    for k, v in timeslices.timeslices.items():
        split_name = k.split(".")
        pack_timeslice_inner(final_dict, split_name, v)

    final_dict["level_names"] = timeslices.level_names
    return final_dict
