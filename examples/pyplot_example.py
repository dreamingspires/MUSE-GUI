import PySimpleGUI as sg

from muse_gui.frontend.widget_funcs.plotting import (
    GuiFigureElements,
    generate_plot,
    generate_plot_layout,
)

figure_elems = GuiFigureElements(canvas=generate_plot())

plot_layout = generate_plot_layout(figure_elems, "canvas")

window = sg.Window(
    "Demo Application - Embedding Matplotlib In PySimpleGUI", plot_layout, finalize=True
)

figure_elems.draw_figures_in_window(window)

event, values = window.read()

window.close()
