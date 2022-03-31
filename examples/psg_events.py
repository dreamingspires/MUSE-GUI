import PySimpleGUI as sg
from pydantic import BaseModel
from typing import List


class Region(BaseModel):
    name: str

    class Config:
        frozen = True


class RegionExistsError(RuntimeError):
    pass


class BaseDataModel:
    """
    TODO: Unused
    """

    def __init__(self):
        self._listeners = []

    def subscribe(self, cb):
        self._listeners.append(cb)

    def notifyAll(self):
        for l in self._listeners:
            self.notify(l)

    def notify(self, cb):
        cb()


class RegionModel(BaseDataModel):
    def __init__(self, regions: List[Region] = []):
        super().__init__()
        self._nonce = 0
        self.regions = {}
        self.add(regions)

    def add(self, regions: List[Region]):
        current = self._nonce
        for r in regions:
            if r not in self.regions:
                self.regions[r] = self._nonce
                self._nonce += 1
        return self._nonce - current

    def exists(self, r: Region):
        return r in self.regions

    def update(self, old: Region, new: Region):
        idx = self.regions.pop(old)
        self.regions[new] = idx

    def remove(self, regions):
        _ = [self.regions.pop(r, None) for r in regions]

    def notify(self, cb):
        cb(self.regions)


class RegionView:
    def __init__(self, window) -> None:
        self.window = window
        self.window['-region-listbox-'].bind(
            '<Double-Button-1>', 'doubleclick-')

    def update_listbox(self, regions):
        self.window['-region-listbox-'].update(regions)
        pass

    def update_edit_btn(self, disabled: bool):
        self.window['-region-edit-'].update(disabled=disabled)

    def status(self, status):
        self.window['-status-'].update(status)

    @staticmethod
    def get_region_tab():
        _left = [
            [sg.Listbox([], select_mode=sg.LISTBOX_SELECT_MODE_EXTENDED,
                        expand_y=True, expand_x=True, enable_events=True, key="-region-listbox-")],
            [sg.Push(), sg.Button('Add...', key='-region-add-'), sg.Button(
                'Edit', disabled=True, key='-region-edit-'), sg.Button('Delete', key='-region-delete-')],
        ]
        _help = (
            'Tip:\n'
            '\n'
            'Add new regions by using the "Add" button.\n'
            '\n'
            'Delete region(s) by selecting them and deleting it.\n'
            '\n'
            'Edit region by selecting a row and clicking "Edit"'
        )
        _right = [
            [sg.Multiline(
                _help,
                size=(None, 12),
                expand_x=True,
                disabled=True,
                write_only=True,
            )],

        ]
        _layout = [
            [sg.Col(_left, expand_x=True, expand_y=True, element_justification="left", justification="left"), sg.Col(
                _right, expand_x=True, expand_y=True)],
        ]
        return sg.Tab("Regions", layout=_layout)


class RegionController:
    def __init__(self, model: RegionModel, view: RegionView):
        self.m = model
        self.v = view

    def show(self):
        self.v.update_listbox(
            [x[0].name for x in sorted(
                self.m.regions.items(), key=lambda x: x[1])]
        )
        self.v.update_edit_btn(disabled=True)

    def __call__(self, event, values, window):
        # Handle listbox event
        current_regions = values['-region-listbox-']
        num_selected = len(current_regions)
        if num_selected == 1:
            # Enable edit button
            self.v.update_edit_btn(disabled=False)
        else:
            # Disable edit button
            self.v.update_edit_btn(disabled=True)

        if event == '-region-listbox-':
            # Selection events
            self.v.status(f'{num_selected} region(s) selected')
            return

        if event == '-region-listbox-doubleclick-':
            # Edit region
            self.handle_update_region(current_regions[0])

        elif event == '-region-add-':
            # Add region
            self.handle_add_region()

        elif event == '-region-edit-':
            # Edit region
            self.handle_update_region(current_regions[0])

        elif event == '-region-delete-':
            # Delete region
            self.handle_remove_regions(current_regions)

        else:
            print(event, values)
            return

    def handle_update_region(self, current: str):
        new = sg.popup_get_text(
            f'Rename {current} as:', 'Edit Region', current)

        if new == None or new == '' or current == new:
            # Cancel
            return
        try:
            new_region = Region(name=new)
            old_region = Region(name=current)
            if self.m.exists(new_region):
                sg.popup_error(
                    f'Cannot rename {current} as {new}: "{new}" already exists!',
                    title="Rename region failed!",
                    auto_close=True,
                    auto_close_duration=5
                )
                self.v.status(f'Edit "{current}" failed!')
                return
            self.m.update(old_region, new_region)

            self.v.status(
                f'Renamed "{current}" -> "{new}"')
            self.show()
        except:
            self.v.status(f'Edit "{current}" failed!')

    def handle_add_region(self):
        regions = sg.popup_get_text(
            'Please enter region(s) to add, seperated by commas', 'Add Region(s)')
        if regions == None or regions.strip() == '':
            return
        try:
            num_regions = self.m.add([Region(name=x.strip())
                                     for x in regions.split(',')])
            self.v.status(f'{num_regions} region(s) added')
            self.show()
        except:
            self.v.status('Add region(s) failed!')

    def handle_remove_regions(self, regions: List[str]):
        self.m.remove([Region(name=x) for x in regions])
        self.show()
        self.v.status(f'{len(regions)} region(s) deleted')


if __name__ == '__main__':
    regions = [
        Region(name=f'R{i}') for i in range(100)
    ]
    rm = RegionModel(regions=regions)
    region_tab = RegionView.get_region_tab()
    layout = [
        [
            sg.TabGroup([
                [region_tab]
            ], expand_x=True, expand_y=True)
        ],
        [
            sg.StatusBar("Ready!", size=(80, 1), expand_x=True,
                         justification='right', key="-status-")
        ]
    ]
    window = sg.Window('MUSE', layout=layout, finalize=True, size=(640, 480), font='roman 16',
                       resizable=True, auto_size_buttons=True, auto_size_text=True)
    window.set_min_size(window.size)
    rv = RegionView(window)
    rc = RegionController(rm, rv)

    rc.show()
    while True:
        event, values = window.read()
        if event == sg.WIN_CLOSED or event == 'Exit':
            break
        if event.startswith('-region'):
            rc(event, values, window)
        else:
            print(event, values)
    window.close()
