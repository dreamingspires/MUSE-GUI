import PySimpleGUI as sg

"""
https://github.com/jason990420/PySimpleGUI-Solution/issues/122
"""


class EditableTable():
    def __init__(self, rows, cols, *args, **kwargs):

        self.nrows = rows
        self.ncols = cols
        kwargs.pop('num_rows', None)

        self.table = sg.Table(num_rows=self.nrows, *args,  **kwargs)
        key = kwargs['key']
        self.input = sg.Input('', expand_x=True, expand_y=True,
                              justification='right',
                              disabled=True,
                              disabled_readonly_background_color='#c3c3c3',
                              pad=0, key=key + ('input',))
        self.frame = sg.Frame('', [[self.input]],
                              border_width=1, pad=0, visible=False)
        self._row = 1
        self._col = 1
        self._editing = False
        self.prefix = key
        self._focus = False

    @property
    def values(self):
        _values = []
        for r in range(1, self.nrows + 1):
            _values.append(
                self.table_widget.item(r, "values")
            )
        return _values

    @values.setter
    def values(self, _val):
        self.nrows = len(_val)
        self.ncols = len(_val[0])
        self.table.update(values=_val)
        self.update_cell_position()

    @property
    def table_widget(self):
        return self.table.Widget

    @property
    def frame_widget(self):
        return self.frame.Widget

    @property
    def row(self):
        return self._row

    @row.setter
    def row(self, val):
        if self._row == val:
            return

        # TODO Validation on num rows
        self._row = val % (self.nrows + 1)
        if self._row == 0:
            self._row = 1
        self.update_cell_position()

    @property
    def col(self):
        return self._col

    @col.setter
    def col(self, val):
        if self._col == val:
            return
        self._col = val % self.ncols
        self.update_cell_position()

    @property
    def cell_text(self):
        return self.table_widget.item(self.row, "values")[self.col]

    @cell_text.setter
    def cell_text(self, val):
        # TODO Validation
        values = list(self.table_widget.item(self.row, 'values'))
        values[self.col] = val
        self.table_widget.item(self.row, values=values)

    @property
    def editing(self):
        return self._editing

    @editing.setter
    def editing(self, val):
        self._editing = val
        if not self._editing:
            self.table.set_focus()
            self._focus = True
            # TODO Hack - read and write again to remove selection
            self.input.update(
                value=self.cell_text,
                select=False,
                move_cursor_to='end',
                disabled=True,
            )
        else:
            self.input.set_focus()
            self.input.update(
                select=True, move_cursor_to='end', disabled=False)

    def bind_resize_handler(self):
        self.table.bind('<B1-Motion>', 'configure')
        self.table.bind('ButtonRelease-1', 'configure-done')

    def unbind_resize_handler(self):
        self.table.unbind('<B1-Motion>')
        self.table.unbind('ButtonRelease-1')

    def bind_handler(self):
        self.input.block_focus(True)
        self.frame.block_focus(True)
        self.input.bind('<Escape>', 'escape')
        self.input.bind('<Return>', 'enter')
        self.input.bind('<Shift-Return>', 'senter')
        self.input.bind('<Up>', 'senter')
        self.input.bind('<Down>', 'enter')
        self.input.bind('<Tab>', 'tab')
        self.input.bind('<Shift-ISO_Left_Tab>', 'stab')

        self.table.bind('<Configure>', 'configure')
        self.table.bind('<Escape>', 'escape')
        self.table.bind('<Return>', 'enter')
        self.table.bind('<Shift-Return>', 'senter')
        self.table.bind('<Up>', 'up')
        self.table.bind('<Down>', 'down')
        self.table.bind('<Left>', 'left')
        self.table.bind('<Right>', 'right')
        self.table.bind('<Tab>', 'tab')
        self.table.bind('<Shift-ISO_Left_Tab>', 'stab')

    def get_layout(self):
        return sg.Col([[
            self.table,
            self.frame
        ]], expand_x=True, expand_y=True)

    def update_cell_position(self):
        bbox = self.table_widget.bbox(self.row, self.col)
        x, y, width, height = bbox
        self.frame_widget.place(
            x=x, y=y, anchor="nw", width=width-2, height=height-1)
        self.input.update(self.cell_text, select=True)

    def edit_cell(self, r, c):
        if r <= 0:
            return
        self.row = r
        self.col = c
        self.editing = True

    def __call__(self, window, event, values):
        e, *params = event
        if e == self.prefix:
            self._handle_table_events(params)
        elif e == self.prefix + ('input',):
            self._handle_input_events(params)

    def _handle_key_events(self, e):
        # Following events are generated by table,
        # so editing must be false
        if e == 'up' or e == 'down':
            self.row += (-1 if e == 'up' else 1)
            return True
        if e == 'left' or e == 'right':
            self.col += (-1 if e == 'left' else 1)
            return True

        # Following events will be generated by table or input
        if e == 'tab' or e == 'stab':
            if self.editing:
                self.cell_text = self.input.get()

            self.col += (-1 if e == 'stab' else 1)

            # Lock focus to table on tab, shift tab
            if not self.editing and self._focus:
                self.table.set_focus()
            return True

        if e == 'enter' or e == 'senter':
            if e == 'enter' and not self.editing:
                self.editing = True
                return True

            if self.editing:
                self.cell_text = self.input.get()

            self.row += (-1 if e == 'senter' else 1)

            if e == 'senter' and not self.editing:
                self.editing = True

            return True

        return False

    def _handle_table_events(self, params):
        e, *rest = params
        print(e, rest)
        if e == '+CLICKED+':
            cell = row, col = rest[0]
            if row is not None and col is not None:
                if self.editing:
                    # Currently editing a cell, copy value
                    self.cell_text = self.input.get()

                return self.edit_cell(row + 1, col)
            elif row is None:
                return self.bind_resize_handler()
        elif e == 'configure':
            return self.update_cell_position()
        elif e == 'configure-done':
            return self.unbind_resize_handler()
        elif e == 'escape':
            self._focus = False
            return
        else:
            status = self._handle_key_events(e)
            if status:
                return
        print('Unhandled - ', e)

    def _handle_input_events(self, params):
        e, *_ = params
        print(e, _)
        if e == 'escape':
            self.editing = False
            return

        status = self._handle_key_events(e)
        if status:
            self.editing = True
