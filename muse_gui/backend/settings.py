from pydantic import BaseModel
from typing import Any, Dict, List, Optional
from carbon_market_model import CarbonMarket
from global_input_files_model import GlobalInputFiles
from main_settings_model import MainSettings
from sectors_model import StandardSectors, PresetSectors, LegacySectors

class SettingsModel(BaseModel):
    main_settings: MainSettings
    global_input_files: GlobalInputFiles
    
