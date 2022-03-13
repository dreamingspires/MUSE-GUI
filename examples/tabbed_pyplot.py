from typing import Dict, List
import PySimpleGUI as sg
from muse_gui.backend.plots import capacity_data_frame_to_plots
from muse_gui.data_defs.commodity import Commodity, CommodityType
from muse_gui.frontend.widget_funcs.data_funcs import CommodityView
from muse_gui.data_defs.sector import Sector, SectorView
from muse_gui.data_defs.technology import Technology, TechnologyView
from muse_gui.data_defs.region import Region, RegionView
from muse_gui.data_defs.agent import Agent, AgentView
from PySimpleGUI.PySimpleGUI import Element
from muse_gui.frontend.widget_funcs.generics import define_tab_group, make_table_layout
from muse_gui.frontend.widget_funcs.plotting import GuiFigureElements, attach_capacity_plot_to_figure, generate_plot,  generate_plot_layout, attach_price_plot_to_figure
from matplotlib.figure import Figure
import pandas as pd

def layout_cycle(layouts: List[List[List[Element]]], prefix = None, visible_column: int = 0) -> List[List[Element]]:
    columns = []
    for i, layout in enumerate(layouts):
        if prefix is None:
            key_str = f'-CYCLE-COLUMN-{str(i)}-'
        else:
            key_str = f'-CYCLE-COLUMN-{prefix.upper()}-{str(i)}-'
        if i ==visible_column:
            columns.append(sg.Column(layout, key=key_str, visible= True, expand_x=True, expand_y = True))
        else:
            columns.append(sg.Column(layout, key=key_str, visible= False, expand_x=True, expand_y = True))
    return [columns]


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


list_of_com = [Commodity(
    commodity='gas',
    commodity_type=CommodityType.energy,
    commodity_name='gas',
    c_emission_factor_co2=0.61,
    heat_rate=1.0,
    unit='Pj')]

list_of_sectors = [
    Sector(
        name='gas',
        priority=1,
    )
]
region = Region(
    name='R1'
)
list_of_regions = [
    region
]
list_of_agents = [
    Agent(
        name='A1',
        type='New',
        region=region,
        share='Agent1'
    ),
    Agent(
        name='A1',
        type='Retrofit',
        region=region,
        share='Agent2'
    )
]
list_of_tech = [
    Technology(
        name='gassupply',
        region=region,
        type='energy',
        fuel='',
        end_use='gas',
    )
]
commodity_views = [CommodityView(x) for x in list_of_com]
region_views = [RegionView(model=x) for x in list_of_regions]
sector_views = [SectorView(model=x) for x in list_of_sectors]
agent_views = [AgentView(model=x) for x in list_of_agents]
tech_views = [TechnologyView(model=x) for x in list_of_tech]

def format_headings(headers: List[str]) -> List[Element]:
    return [sg.Text(header.title().replace('_', ''), expand_x = True) for header in headers]

layout_com = make_table_layout(
    [format_headings(['commodity','commodity_type'])]+
    [[i for i in commodity_view] for commodity_view in commodity_views],
)

out = pd.read_csv('MCACapacity.csv')

fig = generate_plot()

capacity_plots = capacity_data_frame_to_plots(out)

figure_elems = GuiFigureElements(
    figure1 = fig
)

attach_capacity_plot_to_figure(fig ,capacity_plots[0])


plot_layout = generate_plot_layout(figure_elems, 'figure1')

layout = [[define_tab_group({
    "Timeslices": [[sg.Text('Hey')]],
    "Commodities": layout_com,
    "Plot": plot_layout
})]]

window = sg.Window(
    'Window Title', 
    layout, 
    resizable = True,
    size=(10, 100), 
    font = font, 
    auto_size_text=True,
    finalize=True
)


figure_elems.initialise_in_window(window)
figure_elems.draw_figures()

toggle =False
while True:
    event, values = window.read()
    if event == sg.WIN_CLOSED or event == 'Cancel':  # if user closes window or clicks cancel
        break
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


    print('You entered ', values[0])

window.close()
