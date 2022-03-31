from typing import Dict, Optional

import PySimpleGUI as sg

from muse_gui.backend.resources.datastore import Datastore
from muse_gui.frontend.views.agent import AgentView
from muse_gui.frontend.views.available_years import AvailableYearsView
from muse_gui.frontend.views.base import TwoColumnMixin
from muse_gui.frontend.views.commodity import CommodityView
from muse_gui.frontend.views.region import RegionView
from muse_gui.frontend.views.run_view import RunView
from muse_gui.frontend.views.sector import SectorView
from muse_gui.frontend.views.technology import TechnologyView
from muse_gui.frontend.views.timeslices import TimesliceView
from muse_gui.frontend.widgets.tabgroup import TabGroup
from muse_gui.frontend.windows.calc_window import boot_waiting_window
from muse_gui.frontend.windows.plot_window import boot_plot_window
from muse_gui.frontend.windows.utils import Font


def boot_tabbed_window(import_bool: bool, font: Font, file_path: Optional[str] = None):
    if import_bool:
        assert file_path is not None
        datastore = Datastore.from_settings(file_path)
    else:
        datastore = Datastore()
    timeslice_view = TimesliceView(datastore)
    year_view = AvailableYearsView(datastore)
    region_view = RegionView(datastore)
    commodity_view = CommodityView(datastore)
    sector_view = SectorView(datastore)
    agent_view = AgentView(datastore)
    tech_view = TechnologyView(datastore)
    run_view = RunView(datastore)
    tabs: Dict[str, sg.Tab] = {
        "timeslices": timeslice_view,
        "years": year_view,
        "regions": region_view,
        "sectors": sector_view,
        "commodities": commodity_view,
        "agents": agent_view,
        "technologies": tech_view,
        "run": run_view,
    }
    tab_group = TabGroup(tabs, "tg")
    status_bar = sg.StatusBar(
        "Ready!", size=(20, 1), expand_x=True, justification="right", key=("status",)
    )

    layout = tab_group.layout(tuple()) + [[status_bar]]
    window = sg.Window(
        "MUSE",
        layout=layout,
        size=(1000, 800),
        finalize=True,
        font="roman 16",
        resizable=True,
        auto_size_buttons=True,
        auto_size_text=True,
    )
    window.set_min_size(window.size)

    for _tab in tabs.values():
        if isinstance(_tab, TwoColumnMixin):
            _tab.pack()
        _tab.bind_handlers()
        _tab.update(window)
    while True:
        event, values = window.read()
        if event == sg.WIN_CLOSED or event == "Exit":
            window.close()
            break
        elif event == "carbon_market_active":
            if values["carbon_market_active"]:
                window["carbon_market_frame"].update(visible=True)
            else:
                window["carbon_market_frame"].update(visible=False)

        if type(event) is str:
            # Handle event in window level
            pass
        elif event and isinstance(event, tuple):
            if tab_group.should_handle_event(event):
                try:
                    ret = tab_group(window, event, values)
                    if ret:
                        ret, status = ret
                        if ret:
                            # Log exception
                            print(ret)
                            sg.popup_error(str(ret), title="Error")

                        status_bar(status)
                except Exception as e:
                    print(e)
                    if e.__cause__:
                        sg.popup_error(str(e.__cause__), title="Error")
                    else:
                        sg.popup_error(str(e), title="Error")
                    status_bar(str(e))
            else:
                print("Unhandled - ", event)
            if event == ("tg", "run", "run"):
                window.close()
                prices_path, capacity_path = boot_waiting_window(font, datastore)
                boot_plot_window(capacity_path, prices_path, font)
                break
        else:
            print(event)
