from urwid import Widget

class MenuBackground():
    menu: Widget | None = None

    @property
    def name(self) -> str:
        return self.__class__.__name__

    def handle_input(self, key):
        pass
