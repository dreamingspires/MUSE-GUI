class SaveException(Exception):
    def __init__(self, msg=None):
        if msg is None:
            self.msg = "Save failed!. Please fix the errors and try again!"
        elif isinstance(msg, str):
            self.msg = msg
        else:
            self.msg = repr(msg)

    def __str__(self):
        return self.msg
