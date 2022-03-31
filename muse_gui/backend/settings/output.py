from enum import Enum
from typing import Any, Dict, List, Optional, Union

from pydantic import validator

from muse_gui.backend.data.run_model import BaseSettings


class Sink(str, Enum):
    csv = "csv"
    netcfd = "netcfd"
    excel = "excel"
    aggregate = "aggregate"


class Quantity(str, Enum):
    capacity = "capacity"
    prices = "prices"
    supply = "supply"


class Output(BaseSettings):
    quantity: Union[Quantity, Dict[str, Any]] = Quantity.capacity
    sink: Sink = Sink.csv
    filename: Optional[str] = None
    overwrite: bool = True
    keep_columns: Optional[List[str]] = None
    index: Optional[bool] = None

    @validator("filename", pre=True, always=True)
    def validate_filename(cls, value, values):
        if value is None:
            return (
                "{cwd}/{default_output_dir}/{Sector}/"
                + values.quantity
                + "/{year}"
                + values.sink
            )
        else:
            return value
