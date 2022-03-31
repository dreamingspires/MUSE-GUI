from typing import Optional

from muse_gui.backend.data.run_model import BaseSettings


class GlobalInputFiles(BaseSettings):
    projections: str
    global_commodities: str
    regions: Optional[str] = None
