from typing import List

import pandas as pd
import PySimpleGUI as sg
from PySimpleGUI.PySimpleGUI import Element

from muse_gui.backend.plots import (
    capacity_data_frame_to_plots,
    price_data_frame_to_plots,
)
from muse_gui.frontend.widget_funcs.generics import define_tab_group
from muse_gui.frontend.widget_funcs.plotting import (
    GuiFigureElements,
    attach_capacity_plot_to_figure,
    attach_price_plot_to_figure,
    generate_plot,
    generate_plot_layout,
)


def layout_cycle(
    layouts: List[List[List[Element]]], prefix=None, visible_column: int = 0
) -> List[List[Element]]:
    columns = []
    for i, layout in enumerate(layouts):
        if prefix is None:
            key_str = f"-CYCLE-COLUMN-{str(i)}-"
        else:
            key_str = f"-CYCLE-COLUMN-{prefix.upper()}-{str(i)}-"
        if i == visible_column:
            columns.append(
                sg.Column(
                    layout, key=key_str, visible=True, expand_x=True, expand_y=True
                )
            )
        else:
            columns.append(
                sg.Column(
                    layout, key=key_str, visible=False, expand_x=True, expand_y=True
                )
            )
    return [columns]


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
font = ("Arial", 14)

out_cap = pd.read_csv("Results/MCACapacity.csv")
out_price = pd.read_csv("Results/MCAPrices.csv")
fig = generate_plot()

capacity_plots = capacity_data_frame_to_plots(out_cap)
price_plots = price_data_frame_to_plots(out_price)
figure_elems = GuiFigureElements(figure1=fig)

attach_capacity_plot_to_figure(fig, capacity_plots[0])


plot_layout = generate_plot_layout(
    figure_elems,
    "figure1",
    [f"capacity_plot_{c.name}" for c in capacity_plots]
    + [f"price_plot{r.region}" for r in price_plots],
)

layout = [[define_tab_group({"Timeslices": [[sg.Text("Hey")]], "Plot": plot_layout})]]

window = sg.Window(
    "Window Title",
    layout,
    resizable=True,
    size=(1000, 800),
    font=font,
    auto_size_text=True,
    finalize=True,
    element_justification="c",
)


figure_elems.initialise_in_window(window)
figure_elems.draw_figures()

figure_elems.draw_figures()

figure_elems.draw_figures()
# window['figure1'].set_size((1000,2000))
toggle = False
while True:
    event, values = window.read()
    if (
        event == sg.WIN_CLOSED or event == "Cancel"
    ):  # if user closes window or clicks cancel
        break
    if event == "listbox":
        num = window.Element("listbox").Widget.curselection()[0]
        if num >= len(capacity_plots):
            attach_price_plot_to_figure(fig, price_plots[num - len(capacity_plots)])
        else:
            attach_capacity_plot_to_figure(fig, capacity_plots[num])

        figure_elems.draw_figures()
    if event[0:4] == "Back":
        if toggle:
            toggle = False
            print("attach1")
            attach_capacity_plot_to_figure(fig, capacity_plots[0])
            figure_elems.draw_figures()
        else:
            print("attach2")
            toggle = True
            attach_capacity_plot_to_figure(fig, capacity_plots[1])
            figure_elems.draw_figures()
    print("You entered ", values[0])

window.close()
