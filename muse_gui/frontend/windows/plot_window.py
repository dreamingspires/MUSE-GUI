import pandas as pd
import PySimpleGUI as sg

from muse_gui.backend.plots import (
    capacity_data_frame_to_plots,
    price_data_frame_to_plots,
)
from muse_gui.frontend.widget_funcs.plotting import (
    GuiFigureElements,
    attach_capacity_plot_to_figure,
    attach_price_plot_to_figure,
    generate_plot,
    generate_plot_layout,
)
from muse_gui.frontend.windows.utils import Font


def boot_plot_window(capacity_path, price_path, font: Font):
    out_cap = pd.read_csv(capacity_path)
    out_price = pd.read_csv(price_path)
    fig = generate_plot()

    capacity_plots = capacity_data_frame_to_plots(out_cap)
    price_plots = price_data_frame_to_plots(out_price)
    figure_elems = GuiFigureElements(PlotManager=fig)

    attach_capacity_plot_to_figure(fig, capacity_plots[0])

    plot_layout = generate_plot_layout(
        figure_elems,
        "PlotManager",
        [f"capacity_plot_{c.name}" for c in capacity_plots]
        + [f"price_plot{r.region}" for r in price_plots],
    )

    layout = plot_layout

    window = sg.Window(
        "Plot Manager",
        layout,
        resizable=True,
        font=font,
        auto_size_text=True,
        finalize=True,
        element_justification="c",
    )

    figure_elems.initialise_in_window(window)
    figure_elems.draw_figures()

    figure_elems.draw_figures()

    figure_elems.draw_figures()
    window["PlotManager"].set_size((1000, 2000))
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

    window.close()
