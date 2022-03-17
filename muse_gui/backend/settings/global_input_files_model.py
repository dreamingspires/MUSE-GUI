from typing import Optional
from .base import BaseSettings

class GlobalInputFiles(BaseSettings):
    projections: str
    global_commodities: str
    regions: Optional[str] = None