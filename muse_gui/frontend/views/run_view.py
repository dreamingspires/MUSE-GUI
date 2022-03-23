from typing import Optional
from muse_gui.backend.data.run_model import EquilibriumVariable, InterpolationMode, MethodOptions
from muse_gui.frontend.views.base import BaseView
import PySimpleGUI as sg

def get_col1_layout():
    return [
        [
            sg.Text('Regions Selected: '), 
            sg.Push(),
            sg.Listbox(
                values = ["R1", "R2"],
                default_values = [],
                select_mode = "multiple",
                size = (50,5)
            )
        ],
        [
            sg.Text('Time Framework: '),
            sg.Push(), 
            sg.Listbox(
                values = ["2010", "2020"],
                default_values = [],
                select_mode = "multiple",
                size = (50,5)
            )
        ],
        [
            sg.Text('Interest Rate: '), 
            sg.Push(),
            sg.Input()
        ],
        [
            sg.Text('Interpolation Mode: '), 
            sg.Push(),
            sg.Combo(
                [e.value for e in InterpolationMode],
                default_value = InterpolationMode.linear.value
            )
        ],
        [
            sg.Text('Log Level: '), 
            sg.Push(),
            sg.Input(
                default_text = 'info'
            )
        ],
        [
            sg.Text('Equilibrium Variable: '), 
            sg.Push(),
            sg.Combo(
                [e.value for e in EquilibriumVariable],
                default_value = EquilibriumVariable.demand.value
            )
        ],
        [
            sg.Text('Maximum Iterations: '), 
            sg.Push(),
            sg.Input(
                default_text = '3'
            )
        ],
        [
            sg.Text('Tolerance: '), 
            sg.Push(),
            sg.Input(
                default_text = '0.1'
            )
        ],
        [
            sg.Text('Tolerance Unmet Demand: '), 
            sg.Push(),
            sg.Input(
                default_text = '-0.1'
            )
        ],
        [
            sg.Text('Foresight: '), 
            sg.Push(),
            sg.Input(
                default_text = '0'
            )
        ],
        [
            sg.Text('Excluded Commodities: '),
            sg.Push(), 
            sg.Listbox(
                values = ["Electric", "Gas"],
                default_values = [],
                select_mode = "multiple",
                size = (50,5)
            )
        ]
    ]

def get_col2_layout(key_prefix):
    return [
        [
            sg.Checkbox(
                'Activate carbon market', 
                key='carbon_market_active',
                enable_events = True
            )
        ],
        [
            sg.Frame(
                'Carbon Market',
                key='carbon_market_frame',
                visible=False,
                layout = [
                    [
                        sg.Text('Commodities'),
                        sg.Listbox(
                            values = ["Electric", "Gas"],
                            default_values = [],
                            select_mode = "multiple",
                            size = (50,5)
                        )
                    ],
                    [
                        sg.Checkbox('Control undershoot')
                    ],
                    [
                        sg.Checkbox('Control overshoot')
                    ],
                    [
                        sg.Combo(
                            [e.value for e in MethodOptions],
                            default_value = MethodOptions.linear.value
                        )
                    ]
                ]
            )
        ],
        
    ]

class RunView(BaseView):
    def layout(self, key_prefix):
        return [
            [
                sg.Column(
                    get_col1_layout(),
                    expand_x = True,
                    expand_y = True,
                    size = (10,10)
                ),
                sg.Column(
                    get_col2_layout(
                        key_prefix
                    ),
                    expand_x = True,
                    expand_y = True,
                    size = (10,10)
                )
            ],
            [
                sg.Push(), sg.Button('RunMuse', key = (*key_prefix,'button'), size = (20,2)), sg.Push()]
        ]
    def _prefixf(self, k: Optional[str] = None):
        if k is None:
            return 'run_view'
        else:
            return (k, 'run_view')
    def bind_handlers(self):
        pass
    def update(self, v):
        pass