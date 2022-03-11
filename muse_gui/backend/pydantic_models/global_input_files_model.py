from pydantic import BaseModel

class GlobalInputFiles(BaseModel):
    # all should be paths to csv files
    projections: str = None
    regions: str = None
    global_commodities:str = None