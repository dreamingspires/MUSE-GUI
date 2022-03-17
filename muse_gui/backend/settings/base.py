from pydantic import BaseModel

class BaseSettings(BaseModel):
    class Config:
        use_enum_values = True