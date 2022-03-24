from typing import Dict
import PySimpleGUI as sg
from muse_gui.backend.data.commodity import Commodity, CommodityPrice, CommodityType
from muse_gui.backend.data.region import Region
from muse_gui.backend.data.timeslice import AvailableYear
from muse_gui.backend.resources.datastore import Datastore
from muse_gui.frontend.views.available_years import AvailableYearsView
from muse_gui.frontend.views.base import BaseView, TwoColumnMixin
from muse_gui.frontend.views.technology import TechnologyView
from muse_gui.frontend.views.timeslices import TimesliceView
from muse_gui.frontend.widgets.tabgroup import TabGroup
from muse_gui.frontend.views.region import RegionView
from muse_gui.frontend.views.commodity import CommodityView
from muse_gui.frontend.views.agent import AgentView
from muse_gui.frontend.views.sector import SectorView

if __name__ == '__main__':
    # datastore = Datastore(
    #     available_years=[
    #         AvailableYear(
    #             year=2010,
    #         )
    #     ],
    #     regions=[
    #         Region(name='R1'),
    #         Region(name='R2'),
    #         Region(name='R3')
    #     ],
    #     commodities=[
    #         Commodity(
    #             id='C1',
    #             name='Commodity1',
    #             type=CommodityType.energy,
    #             co2_emission=0,
    #             heat_rate=1.0,
    #             unit='PJ',
    #             price_unit='x1M USD',
    #             commodity_prices=[
    #                 CommodityPrice(
    #                     region_name='R1',
    #                     time=2010,
    #                     value=10
    #                 )
    #             ]
    #         )
    #     ]
    # )
    datastore = Datastore.from_settings('./example_data/settings.toml')
    timeslice_view = TimesliceView(datastore)
    year_view = AvailableYearsView(datastore)
    region_view = RegionView(datastore)
    commodity_view = CommodityView(datastore)
    sector_view = SectorView(datastore)
    agent_view = AgentView(datastore)
    tech_view = TechnologyView(datastore)
    tabs: Dict[str, BaseView] = {
        'timeslices': timeslice_view,
        'years': year_view,
        'regions': region_view,
        'commodities': commodity_view,
        'sectors': sector_view,
        'agents': agent_view,
        'technologies': tech_view,
    }
    tab_group = TabGroup(tabs, 'tg')
    status_bar = sg.StatusBar(
        "Ready!",
        size=(20, 1),
        expand_x=True,
        justification='right',
        key=("status", ))

    layout = tab_group.layout(tuple()) + [[ status_bar ]]
    window = sg.Window('MUSE', layout=layout, finalize=True, font='roman 16',
                       resizable=True, auto_size_buttons=True, auto_size_text=True)
    window.set_min_size(window.size)
    for _tab in tabs.values():
        if isinstance(_tab, TwoColumnMixin):
            _tab.pack()
        _tab.bind_handlers()
        _tab.update(window)
    while True:
        event, values = window.read()
        if event == sg.WIN_CLOSED or event == 'Exit':
            break
        print(event)
        if type(event) is str:
            # Handle event in window level
            pass
        elif event and isinstance(event, tuple):
            # Non empty tuple
            if tab_group.should_handle_event(event):
                ret = tab_group(window, event, values)
                if ret:
                    ret, status = ret
                    if ret:
                        # Log exception
                        print(ret)
                    status_bar(status)
            else:
                print('Unhandled - ', event)
                pass
    window.close()
