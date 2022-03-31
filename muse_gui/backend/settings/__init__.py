from typing import Annotated, Any, Dict, List, Optional, Union

from pydantic import BaseModel, Field, PositiveInt, validator

from muse_gui.backend.data.run_model import BaseSettings, RunModel
from muse_gui.backend.resources.datastore.exceptions import LevelNameMismatch
from muse_gui.backend.utils import unpack_timeslice

from .global_input_files_model import GlobalInputFiles
from .output import Output
from .sectors_model import LegacySector, PresetSector, StandardSector


class SettingsModel(RunModel):
    global_input_files: GlobalInputFiles
    sectors: Dict[
        str,
        Annotated[
            Union[StandardSector, PresetSector, LegacySector],
            Field(discriminator="type"),
        ],
    ]
    timeslices: Dict[str, Any]

    @validator("timeslices")
    def validate_timeslice(cls, v):
        time_slice_info = unpack_timeslice(v)
        time_slice_names = list(time_slice_info.timeslices.keys())
        break_down_names = [i.split(".") for i in time_slice_names]
        for break_down_name in break_down_names:
            if len(break_down_name) != len(time_slice_info.level_names):
                raise LevelNameMismatch(time_slice_info.level_names, break_down_name)
        return v

    outputs: Optional[List[Output]] = None
