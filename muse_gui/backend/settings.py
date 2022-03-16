from pydantic import BaseModel, Field
from typing import Annotated, Any, Dict, List, Optional, Union
from settings_models.carbon_market_model import CarbonMarket
from settings_models.global_input_files_model import GlobalInputFiles
from settings_models.main_settings_model import MainSettings
from settings_models.sectors_model import PresetSector, LegacySector, StandardSector

class SettingsModel(MainSettings):
    carbon_budget_control: Optional[CarbonMarket] = None
    global_input_files: Optional[GlobalInputFiles] = None
    sectors: Dict[str, Annotated[Union[StandardSector, PresetSector, LegacySector], Field(discriminator='type')]] = None
    timeslices: Dict[str, Any]
    pass
    
