from muse_gui.backend.resources import Datastore
from muse_gui.backend.data.region import Region
from muse_gui.backend.data.timeslice import LevelName, Timeslice

data_store = Datastore.from_settings('./example_data/settings.toml')
data_store.export_to_folder('./Output/Test')
print(data_store.run_settings)