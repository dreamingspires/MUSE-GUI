from functools import partial
from typing import List

import PySimpleGUI as sg
from PySimpleGUI import Element

from muse_gui.frontend.views.exceptions import SaveException

from ...backend.data.timeslice import AvailableYear
from ...backend.resources.datastore import Datastore
from ...backend.resources.datastore.exceptions import KeyAlreadyExists
from ..widgets.listbox import ListboxWithButtons
from .base import BaseView, TwoColumnMixin


class AvailableYearsView(TwoColumnMixin, BaseView):
    def __init__(self, model: Datastore):
        super().__init__("available_years")
        self._parent_model = model
        self.model = model.available_year
        self._year_list_maker = partial(ListboxWithButtons)
        self._selected = None

    def update(self, window=None):

        # Model years
        _model_years = self.model.list()

        # Sort the list of model years
        sorted_years = sorted(_model_years, key=lambda x: int(x))

        selection_index = []
        if self._selected is not None:
            # Set the correct selected year
            selection_index = [sorted_years.index(self._selected)]

        # Update the UI elements
        self._year_list.values = sorted_years
        self._year_list.indices = selection_index

    def layout(self, prefix) -> List[List[Element]]:
        if not self._layout:
            self.prefix = prefix
            # Left column
            self._year_list = self._year_list_maker()

            # Right Column
            _help = (
                "Simulation years:\n"
                "\n"
                "Years over which you would like to define parameters and run the simulation for.\n"
                "Tip:\n"
                "\n"
                'Add new years by using the "Add" button.\n'
                "\n"
                'You can run the simulation for a subset of years (see "Run" tab)\n'
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
                self._year_list.layout(self._prefixf()), expand_y=True
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
            selected = self._year_list.selected
            if len(selected):
                self._selected = selected[-1]

        elif _event == "add":
            # Add event
            # Show pop up and add years to datastore
            return self._handle_add_years()

        elif _event == "delete":
            # Delete event
            # Show popup with dependents and confirm delete
            return self._handle_delete_years()
        else:
            # Pass it down?
            print("Unhandled event - ", event)
        return None

    def _handle_delete_year_internal(self, year):
        """
        Internal function that deletes the year
        returns True / False based on whether year was deleted or not
        """
        # Compute forward dependencies
        deps = self.model.forward_dependents_recursive(self.model.read(year))

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
                f"Deleting years {year} will result in deleting the following:\n",
                f"{dep_string}"
                f'(You can possibly filter the simulation years instead in the "Run" tab)\n\n'
                f"Delete anyway?\n",
                title="Warning!",
            )
            if ret and ret == "Yes":
                self.model.delete(year)
                return True
            else:
                return False
        else:
            self.model.delete(year)
            return True

    def _handle_delete_years(self):
        selected_years = self._year_list.selected
        if len(selected_years) == 0:
            return

        counter = 0
        for y in selected_years:
            counter += self._handle_delete_year_internal(y)

        if counter:
            # When deleting the first item, this forces it to keep
            # the next item selected rather than deselecting
            view_years = self._year_list.values
            selected_index = self._year_list.indices

            current_idx = selected_index[-1]
            new_idx = current_idx - (1 if current_idx else -1)
            if new_idx >= len(view_years):
                self._selected = None
            else:
                self._selected = view_years[new_idx]
            self.update()

        return None, f"{counter} year(s) deleted"

    def _handle_add_years(self):
        years = sg.popup_get_text(
            "Please enter year(s) to add, seperated by commas", "Add Simulation Year(s)"
        )
        if years == None or years.strip() == "":
            return None, "0 years added"
        try:
            counter = 0
            for x in years.split(","):
                _year = x.strip()
                if not _year:
                    # Empty values?
                    continue
                try:
                    self.model.create(AvailableYear(year=_year))
                    counter += 1
                    self._selected = _year
                except KeyAlreadyExists:
                    pass

            self.update()
            return None, f"{counter} year(s) added"

        except Exception as e:
            raise SaveException("Add Year(s) failed!") from e
