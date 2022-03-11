from typing import List
import PySimpleGUI as sg
from muse_gui.data_defs.commodity import Commodity, CommodityType
from muse_gui.frontend.widget_funcs.data_funcs import CommodityView
from muse_gui.data_defs.sector import Sector, SectorView
from muse_gui.data_defs.technology import Technology, TechnologyView
from muse_gui.data_defs.region import Region, RegionView
from muse_gui.data_defs.agent import Agent, AgentView
from PySimpleGUI.PySimpleGUI import Element
from muse_gui.frontend.widget_funcs.generics import define_tab_group, make_table_layout
from muse_gui.frontend.widget_funcs.plotting import GuiFigureElements, generate_plot,  generate_plot_layout
from matplotlib.figure import Figure
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


figure_elems = GuiFigureElements(
    canvas = generate_plot()
)

plot_layout = generate_plot_layout(figure_elems, 'canvas')

layout = [[define_tab_group({
    "Timeslices": [[sg.Text('Hey')]],
    "Commodities": layout_com,
    "Plot": plot_layout
})]]

window = sg.Window(
    'Window Title', 
    layout, 
    resizable = True,
    size=(500,500), 
    font = font, 
    auto_size_buttons = True, 
    auto_size_text=True,
    finalize=True
)
figure_elems.draw_figures_in_window(window)

while True:

    event, values = window.read()
    if event == sg.WIN_CLOSED or event == 'Cancel':  # if user closes window or clicks cancel
        break
    print('You entered ', values[0])

window.close()
