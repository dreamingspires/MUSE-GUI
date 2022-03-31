from functools import partial
from math import inf
from typing import List

import PySimpleGUI as sg
from PySimpleGUI import Element

from muse_gui.frontend.views.exceptions import SaveException

from ...backend.data.region import Region
from ...backend.resources.datastore import Datastore
from ...backend.resources.datastore.exceptions import KeyAlreadyExists
from ..widgets.listbox import ListboxWithButtons
from .base import BaseView, TwoColumnMixin


class RegionView(TwoColumnMixin, BaseView):
    def __init__(self, model: Datastore):
        super().__init__("region")
        self._parent_model = model
        self.model = model.region
        self._region_list_maker = partial(ListboxWithButtons)
        self._selected = -1

    def update(self, window=None):
        # model regions
        _regions = self.model.list()

        self._selected = min(self._selected, len(_regions) - 1)

        self._region_list.values = _regions
        self._region_list.indices = [self._selected] if self._selected != -1 else None

    def layout(self, prefix) -> List[List[Element]]:
        if not self._layout:
            self.prefix = prefix
            # Left column
            self._region_list = self._region_list_maker()

            # Right Column
            _help = (
                "Simulation regions:\n"
                "\n"
                'Add new regions by using the "Add" button.\n'
                "\n"
                "Delete region(s) by selecting them and deleting it.\n"
                "\n"
                'Tip: You can filter regions in "Run" tab rather than deleting'
            )
            _right = [
                [
                    sg.Multiline(
                        _help,
                        size=(25, 12),
                        expand_x=True,
                        disabled=True,
                        write_only=True,
                        no_scrollbar=True,
                    )
                ],
            ]
            self.column_1 = sg.Column(
                self._region_list.layout(self._prefixf()), expand_y=True
            )
            self.column_2 = sg.Column(_right, expand_x=True, expand_y=True)
            self._layout = [[self.column_1, self.column_2]]
        return self._layout

    def bind_handlers(self):
        pass

    def __call__(self, window, event, values):
        print("Region view handling - ", event)

        address = event
        if event[0] and isinstance(event[0], tuple):
            address = event[0]

        _event = address[len(self._prefixf()) :][0]

        if _event == "listbox":
            # Selection event
            indices = self._region_list.indices
            if len(indices):
                self._selected = indices[0]

        elif _event == "add":
            # Add event
            # Show pop up and add regions to datastore
            return self._handle_add_regions()

        elif _event == "delete":
            # Delete event
            # Show popup with dependents and confirm delete
            return self._handle_delete_regions()
        else:
            # Pass it down?
            print("Unhandled event - ", event)
        return None

    def _handle_delete_region_safe(self, region):
        """
        Internal function that deletes the region
        returns True / False based on whether region was deleted or not
        """
        # Compute forward dependencies
        deps = self.model.forward_dependents_recursive(self.model.read(region))

        # Check if deps are empty
        empty_deps = True
        dep_string = ""
        for d in deps:
            if len(deps[d]):
                empty_deps = False
                dep_string += f"{d}:\n"
                dep_string += ",".join(deps[d])
                dep_string += "\n\n"

        # Show popup to confirm
        if not empty_deps:
            ret = sg.popup_yes_no(
                f"Deleting region {region} will result in the following being deleted:\n",
                f"{dep_string}"
                f'(You can possibly filter the simulation regions instead in the "Run" tab)\n\n'
                f"Delete anyway?\n",
                title="Warning!",
            )
            if ret and ret == "Yes":
                self.model.delete(region)
                return True
            else:
                return False
        else:
            self.model.delete(region)
            return True

    def _handle_delete_regions(self):
        selected_regions = self._region_list.selected
        if len(selected_regions) == 0:
            return

        counter = 0
        for r in selected_regions:
            counter += self._handle_delete_region_safe(r)

        if counter:
            self._selected = max(0, self._selected - 1)
            self.update()
        return None, f"{counter} region(s) deleted"

    def _handle_add_regions(self):
        regions = sg.popup_get_text(
            "Please enter region(s) to add, seperated by commas", "Add Region(s)"
        )
        if regions == None or regions.strip() == "":
            return None, "0 regions added"
        try:
            counter = 0
            for x in regions.split(","):
                _region = x.strip()
                if not _region:
                    # Empty values?
                    continue
                try:
                    self.model.create(Region(name=_region))
                    counter += 1
                except KeyAlreadyExists:
                    pass

            self._selected = inf
            self.update()
            return None, f"{counter} region(s) added"

        except Exception as e:
            raise SaveException("Add region(s) failed!") from e
