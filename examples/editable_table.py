import PySimpleGUI as sg
from muse_gui.frontend.widget_funcs.table import EditableTable


if __name__ == '__main__':

    headings = [f'Col{idx}' for idx in range(10)]
    tvalues = [[0 for _ in range(10)] for _ in range(10)]
    etable = EditableTable(
        10, 10,
        key=('edit-table',),
        values=tvalues, headings=headings,
        expand_x=True, expand_y=True, pad=0, enable_click_events=True, hide_vertical_scroll=True,
        select_mode=sg.TABLE_SELECT_MODE_NONE
    )
    layout = [
        [etable.get_layout()],
        [sg.Input()],
        [sg.Button('Read', key='read'), sg.Button(
            'Zero', key='zero'), sg.Button('Write', key='write')]
    ]

    window = sg.Window('Editable Table', layout, use_default_focus=True,
                       font='Any 16', resizable=True, finalize=True)
    window.set_min_size(window.size)
    # layout[0][0].block_focus(True)
    etable.bind_handler()
    while True:
        event, values = window.read()
        if event in (sg.WIN_CLOSED, 'Exit'):
            break
        print(event, values)
        if event == 'read':
            tvalues = etable.values
        elif event == 'write':
            etable.values = tvalues
        elif event == 'zero':
            etable.values = [[0 for _ in range(10)] for _ in range(10)]

        elif event and isinstance(event, tuple):
            address, *rest = event[0] if event[0] and isinstance(
                event[0], tuple) else event
            if address == 'edit-table':
                etable(window, event, values)

    window.close()
