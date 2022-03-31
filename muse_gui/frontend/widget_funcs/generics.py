from typing import Dict, List

import PySimpleGUI as sg
from PySimpleGUI.PySimpleGUI import Element


def make_table_layout(rows: List[List[Element]]) -> List[List[sg.Column]]:
    def make_column(elems: List[Element]) -> sg.Column:
        return sg.Column([[elem] for elem in elems], expand_x=True, expand_y=True)

    assert all([len(row) == len(rows[0]) for row in rows])
    columns: List[List[Element]] = list(map(list, zip(*rows)))
    return [[make_column(i) for i in columns]]


def define_tab_group(tab_layouts: Dict[str, List[List[Element]]]) -> sg.TabGroup:
    tabs = [
        sg.Tab(tab_name, layout, key=f"-TAB-{tab_name.upper()}-")
        for tab_name, layout in tab_layouts.items()
    ]
    return sg.TabGroup([tabs], expand_x=True, expand_y=True)
