from typing import Dict, Optional
import PySimpleGUI as sg
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
import pandas as pd
from typing import Dict
import PySimpleGUI as sg
from muse_gui.backend.plots import capacity_data_frame_to_plots, price_data_frame_to_plots

from muse_gui.frontend.widget_funcs.plotting import GuiFigureElements, attach_capacity_plot_to_figure, generate_plot,  generate_plot_layout, attach_price_plot_to_figure
import pandas as pd
import time

def boot_initial_window(font) -> Optional[bool]:
    layout = [[
        sg.Col(
            [[sg.Button('Import Toml', key=True, font=font, size= (15,4))]], pad=1
        ), 
        sg.Col(
            [[sg.Button('Start New Project', key=False, font = font, size= (15,4))]], pad=1
        )
    ]]
    window = sg.Window(
        'Plot Manager', 
        layout, 
        resizable = True,
        finalize=True,
        element_justification='c'
    )
    event, values = window.read()
    window.close()
    if event == sg.WIN_CLOSED:
        return None
    return True


def boot_waiting_window(font):
    window = sg.Window(
        'Waiting', 
        [[sg.Text('Calculating MUSE')]], 
        resizable = True,
        font = font, 
        auto_size_text=True,
        finalize=True,
        element_justification='c'
    )
    time.sleep(2)
    window.close()
    

def boot_plot_window():
    out_cap = pd.read_csv('MCACapacity.csv')
    out_price = pd.read_csv('MCAPrices.csv')
    fig = generate_plot()

    capacity_plots = capacity_data_frame_to_plots(out_cap)
    price_plots = price_data_frame_to_plots(out_price)
    figure_elems = GuiFigureElements(
        PlotManager = fig
    )

    attach_capacity_plot_to_figure(fig ,capacity_plots[0])


    plot_layout = generate_plot_layout(figure_elems, 'PlotManager', [f'capacity_plot_{c.name}' for c in capacity_plots]+[f'price_plot{r.region}' for r in price_plots])

    layout = plot_layout

    window = sg.Window(
        'Plot Manager', 
        layout, 
        resizable = True,
        font = font, 
        auto_size_text=True,
        finalize=True,
        element_justification='c'
    )


    figure_elems.initialise_in_window(window)
    figure_elems.draw_figures()

    figure_elems.draw_figures()

    figure_elems.draw_figures()
    window['PlotManager'].set_size((1000,2000))
    toggle =False
    while True:
        event, values = window.read()
        if event == sg.WIN_CLOSED or event == 'Cancel':  # if user closes window or clicks cancel
            break
        if event == 'listbox':
            num = window.Element('listbox').Widget.curselection()[0]
            if num >= len(capacity_plots):
                attach_price_plot_to_figure(fig ,price_plots[num-len(capacity_plots)])
            else:
                attach_capacity_plot_to_figure(fig ,capacity_plots[num])

            figure_elems.draw_figures()
        if event[0:4] == 'Back':
            if toggle:
                toggle = False
                print('attach1')
                attach_capacity_plot_to_figure(fig ,capacity_plots[0])
                figure_elems.draw_figures()
            else:
                print('attach2')
                toggle = True
                attach_capacity_plot_to_figure(fig ,capacity_plots[1])
                figure_elems.draw_figures()

    window.close()

def boot_tabbed_window(import_bool: bool):
    if import_bool:
        datastore = Datastore.from_settings('./example_data/settings.toml')
    else:
        datastore = Datastore()
    timeslice_view = TimesliceView(datastore)
    year_view = AvailableYearsView(datastore)
    region_view = RegionView(datastore)
    commodity_view = CommodityView(datastore)
    sector_view = SectorView(datastore)
    agent_view = AgentView(datastore)
    tech_view = TechnologyView(datastore)
    tabs: Dict[str, sg.Tab] = {
        'timeslices': timeslice_view,
        'years': year_view,
        'regions': region_view,
        'commodities': commodity_view,
        'sectors': sector_view,
        'agents': agent_view,
        'technologies': tech_view,
        'run': RunView()
    }
    tab_group = TabGroup(tabs, 'tg')
    status_bar = sg.StatusBar(
        "Ready!",
        size=(20, 1),
        expand_x=True,
        justification='right',
        key=("status", ))



    layout = tab_group.layout(tuple()) + [[ status_bar ]]
    window = sg.Window('MUSE', layout=layout, size=(1000,800), finalize=True, font='roman 16',
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
            window.close()
            break
        if type(event) is str:
            # Handle event in window level
            pass
        elif event == ('tg', 'button'):
            window.close()
            boot_waiting_window(font)
            boot_plot_window()
            break
        elif event and isinstance(event, tuple):
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
        else:
            print(event)
        


if __name__ == '__main__':
# Add your new theme colors and settings

    light = '#E7F5F9'
    dark = '#D8EEF4'
    darker = '#CEEAF2'
    black = '#000000'
    custom_theme = {'BACKGROUND': light,
                    'TEXT': black,
                    'INPUT': dark,
                    'TEXT_INPUT': black,
                    'SCROLL': '#c7e78b',
                    'BUTTON': ('white', '#709053'),
                    'PROGRESS': ('#01826B', '#D0D0D0'),
                    'BORDER': 2,
                    'SLIDER_DEPTH': 0,
                    'PROGRESS_DEPTH': 0}

    # Add your dictionary to the PySimpleGUI themes
    sg.theme_add_new('CustomTheme', custom_theme)

    # Switch your theme to use the newly added one. You can add spaces to make it more readable
    sg.theme('CustomTheme')
    font = ('Arial', 14)

    class RunView(BaseView):
        def layout(self, key_prefix):
            return [[sg.Button('RunMuse', key = (*key_prefix,'button'))]]
        def _prefixf(self, k: Optional[str] = None):
            if k is None:
                return 'run_view'
            else:
                return (k, 'run_view')
        def bind_handlers(self):
            pass
        def update(self, v):
            pass
    import_bool = boot_initial_window(font = font)
    if import_bool is not None:
        boot_tabbed_window(import_bool)
