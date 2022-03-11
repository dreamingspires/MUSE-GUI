from typing import List
import PySimpleGUI as sg
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.figure import Figure
from PySimpleGUI.PySimpleGUI import Element

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

def draw_figure(canvas, figure):
    figure_canvas_agg = FigureCanvasTkAgg(figure, canvas)
    figure_canvas_agg.draw()
    figure_canvas_agg.get_tk_widget().pack(side='top', fill='both', expand=1)
    return figure_canvas_agg

def figure_to_layout(fig: Figure, key: str = 'canvas') -> List[List[Element]]:
    def figure_to_canvas(fig: Figure, key: str = 'canvas') -> sg.Canvas:
        figure_x, figure_y, figure_w, figure_h = fig.bbox.bounds
        return sg.Canvas(size=(figure_w, figure_h), key=key)
    figure_x, figure_y, figure_w, figure_h = fig.bbox.bounds
    return [[sg.Text('Plot test', font='Any 18')],
        [figure_to_canvas(fig)],
        [sg.OK(pad=((figure_w / 2, 0), 3), size=(4, 2))]]

fig = generate_plot() 

layout = figure_to_layout(fig, key='canvas')

window = sg.Window('Demo Application - Embedding Matplotlib In PySimpleGUI',
    layout, finalize=True)

fig_photo = draw_figure(window['canvas'].TKCanvas, fig)

event, values = window.read()

window.close()