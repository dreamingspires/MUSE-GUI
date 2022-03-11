import json
import toml
from muse.settings_model import SettingsModel
toml_struct = toml.load('example.toml')
print(json.dumps(toml_struct, indent=2))
pydantic_struct = SettingsModel.parse_obj(toml_struct)
print('#############')
print(json.dumps(pydantic_struct.dict(), indent=2))


