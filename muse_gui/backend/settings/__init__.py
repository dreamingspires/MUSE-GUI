from pydantic import BaseModel, Field
from typing import Annotated, Any, Dict, List, Optional, Union
from .carbon_market_model import CarbonMarket
from .global_input_files_model import GlobalInputFiles
from .main_settings_model import MainSettings
from .sectors_model import PresetSector, LegacySector, StandardSector

class SettingsModel(MainSettings):
    carbon_budget_control: Optional[CarbonMarket] = None
    global_input_files: Optional[GlobalInputFiles] = None
    sectors: Optional[Dict[str, Annotated[Union[StandardSector, PresetSector, LegacySector], Field(discriminator='type')]]] = None
    timeslices: Dict[str, Any]
