from typing import List

import PySimpleGUI as sg

from muse_gui.frontend.widgets.listbox import DualListbox


def show_dual_listbox(title: str, v_one: List[str] = [], v_two: List[str] = []):
    dual_listbox = DualListbox(values1=v_one, values2=v_two)

    _layout = [
        [
            sg.Text("Available", auto_size_text=True),
            sg.Push(),
            sg.Text("To be associated", auto_size_text=True),
        ],
    ] + dual_listbox.layout(prefix=("dual",))

    window = sg.Window(
        title,
        _layout,
        resizable=True,
        finalize=True,
        auto_size_buttons=True,
        auto_size_text=True,
    )
    window.set_min_size(window.size)
    dual_listbox.bind_handlers()

    return_values = (v_one, v_two)
    while True:
        event, values = window.read()
        if event == sg.WIN_CLOSED or event == "Exit":
            break
        if type(event) is str:
            # Handle event in window level
            # There should be technially nothing to handle
            print("Window handling - ", event)
        elif event and isinstance(event, tuple):
            # Non empty tuple
            if dual_listbox.should_handle_event(event):
                ret = dual_listbox(window, event, values)
                if ret:
                    _ret, _val = ret
                    if _ret == "done":
                        return_values = _val
                        break
                    elif _ret == "cancel":
                        break
                    else:
                        # ignore other events?
                        pass
            else:
                print("Unhandled - ", event)
        else:
            print("Unhandled event at window - ", event)
    window.close()
    return return_values


if __name__ == "__main__":
    l1 = ["1", "2", "3"]
    l2 = ["4", "5", "6"]

    ret = show_dual_listbox("Regions", v_one=l1, v_two=l2)
    print(ret)
