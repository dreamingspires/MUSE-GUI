import PySimpleGUI as sg

from muse_gui.data_defs.commodity import Commodity, CommodityType
from muse_gui.frontend.widget_funcs.generics import make_table_layout

# Add your new theme colors and settings
light = "#E7F5F9"
dark = "#D8EEF4"
darker = "#CEEAF2"
black = "#000000"
custom_theme = {
    "BACKGROUND": light,
    "TEXT": black,
    "INPUT": dark,
    "TEXT_INPUT": black,
    "SCROLL": "#c7e78b",
    "BUTTON": ("white", "#709053"),
    "PROGRESS": ("#01826B", "#D0D0D0"),
    "BORDER": 2,
    "SLIDER_DEPTH": 0,
    "PROGRESS_DEPTH": 0,
}

# Add your dictionary to the PySimpleGUI themes
sg.theme_add_new("CustomTheme", custom_theme)

# Switch your theme to use the newly added one. You can add spaces to make it more readable
sg.theme("CustomTheme")

list_of_com = [
    Commodity(
        commodity="ga",
        commodity_type=CommodityType.energy,
        commodity_name="gas",
        c_emission_factor_co2=0.61,
        heat_rate=1.0,
        unit="Pj",
    )
]

layout = make_table_layout(
    [list(Commodity.heading().values())]
    + [list(i.item().values()) for i in list_of_com],
)

# Create the Window
window = sg.Window("Window Title", layout)
# Event Loop to process "events" and get the "values" of the inputs
while True:
    event, values = window.read()
    if (
        event == sg.WIN_CLOSED or event == "Cancel"
    ):  # if user closes window or clicks cancel
        break
    print("You entered ", values[0])

window.close()
