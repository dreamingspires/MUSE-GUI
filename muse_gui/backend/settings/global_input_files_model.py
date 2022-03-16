from typing import Optional
from pydantic import BaseModel

class GlobalInputFiles(BaseModel):
    # all should be paths to csv files
    projections: Optional[str] = None
    regions: Optional[str] = None
    global_commodities: Optional[str] = None