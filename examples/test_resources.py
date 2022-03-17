from muse_gui.backend.resources import Datastore
from muse_gui.data_defs.region import Region
from muse_gui.data_defs.timeslice import LevelName, Timeslice

data_store = Datastore()
data_store2 = Datastore(
    [Region(name='R1')], 
    level_names=[LevelName(level="Hour"), LevelName(level="minute")], 
    timeslices=[Timeslice(name='evening.12',value=1460.0)]
)

data_store.region.create(Region(name='R2'))
print(data_store.region.read('R2'))

#data_store.region.delete('R2')
print(data_store.region.read('R2'))
print(data_store2.timeslice.back_dependents_recursive(Timeslice(name='evening.12',value=1460.0)))
data_store.region.update('R2',Region(name='R1'))
