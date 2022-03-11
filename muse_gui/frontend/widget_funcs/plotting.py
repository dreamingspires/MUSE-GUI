from typing import List, Tuple
import PySimpleGUI as sg
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.figure import Figure
from PySimpleGUI.PySimpleGUI import Element
from muse_gui.backend.plots import CapacityPlot, PricePlot

def _draw_figure(canvas, figure):
    figure_canvas_agg = FigureCanvasTkAgg(figure, canvas)
    figure_canvas_agg.draw()
    figure_canvas_agg.get_tk_widget().pack(side='top', fill='both', expand=1)
    return figure_canvas_agg

def _figure_to_canvas(fig: Figure, key: str = 'canvas') -> sg.Canvas:
    figure_x, figure_y, figure_w, figure_h = fig.bbox.bounds
    return sg.Canvas(size=(figure_w, figure_h), key=key)

def _get_figure_size(fig: Figure) -> Tuple[float,float]:
    figure_x, figure_y, figure_w, figure_h = fig.bbox.bounds
    return (figure_w,figure_h)

class GuiFigureElements:
    def __init__(self, **figures: Figure) -> None:
        self._figures = figures

    def get_element(self, arg:str):
        return _figure_to_canvas(self._figures[arg], key=arg)

    def get_size(self, arg:str):
        return _get_figure_size(self._figures[arg])

    def draw_figures_in_window(self, window):
        for key, fig in self:
            _draw_figure(window[key].TKCanvas, fig)

    def __iter__(self):
        self._iterator = iter(zip(self._figures.keys(), self._figures.values()))
        return self
    
    def __next__(self):
        return next(self._iterator)


# These are used to demonstate examples, and very replaceable

def generate_plot(title = 'Plot Title', xaxis= 'X-Axis Values', yaxis='Y-Axis Values') -> Figure:
    values_to_plot = (20, 35, 30, 35, 27)
    ind = np.arange(len(values_to_plot))
    width = 0.4
    fig = plt.figure()
    ax = fig.add_subplot(1,1,1)
    p1 = ax.bar(ind, values_to_plot, width)
    ax.set_xlabel(xaxis)
    ax.set_ylabel(yaxis)
    ax.set_title(title)
    ax.set_xticks(ind, ('Item 1', 'Item 2', 'Item 3', 'Item 4', 'Item 5'))
    ax.set_yticks(np.arange(0, 81, 10))
    ax.legend((p1[0],), ('Data Group 1',))
    return fig


def generate_plot_layout(figures: GuiFigureElements, key: str) -> List[List[Element]]:
    return [[sg.Text(key.title(), font='Any 18')],
        [figures.get_element(key)],
        [sg.OK(pad=((figures.get_size(key)[0] / 2, 0), 3), size=(4, 2))]
    ]


def capacity_plot_to_figure(capacity_plot: CapacityPlot) -> Figure:
    assert len(capacity_plot.data) > 0
    fig = plt.figure(num = 3, figsize=(8, 5))
    ax = fig.add_subplot(1,1,1)
    ax.set_xlabel('Year')
    ax.set_ylabel('Capacity')
    ax.set_title(f'Region: {capacity_plot.region}, Agent: {capacity_plot.agent}, Sector: {capacity_plot.sector}')
    axes = []
    headers = []
    for tech, data in capacity_plot.data.items():
        y_vals = list(data['capacity'])
        x_vals = list(data['year'])
        new_ax = ax.plot(x_vals, y_vals)
        axes.append(new_ax)
        headers.append(tech)

    ax.legend(tuple([i[0] for i in axes]), tuple(headers))
    return fig

def price_plot_to_figure(price_plot: PricePlot) -> Figure:
    assert len(price_plot.data) > 0
    fig = plt.figure(num = 3, figsize=(8, 5))
    ax = fig.add_subplot(1,1,1)
    ax.set_xlabel('Year')
    ax.set_ylabel('Price')
    ax.set_title(f'Region: {price_plot.region}')
    axes = []
    headers = []
    for commodity, data in price_plot.data.items():
        y_vals = list(data['prices'])
        x_vals = list(data['year'])
        new_ax = ax.plot(x_vals, y_vals)
        axes.append(new_ax)
        headers.append(commodity)

    ax.legend(tuple([i[0] for i in axes]), tuple(headers))
    return fig