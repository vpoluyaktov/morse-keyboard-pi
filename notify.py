# PopupSelect.py

import npyscreen
from npyscreen import FixedText
from npyscreen.wgNMenuDisplay import HasMenus
import curses


class PopupSelect(FixedText, HasMenus):
    def __init__(self, *args, **kwargs):
        FixedText.__init__(self, *args, **kwargs)
        self.initialize_menus()
        self.menu = self.add_menu()

        self.add_handlers({
            curses.ascii.NL: self.display_menu,
        })

        # Add some items to the menu for demonstration purposes
        for item in ['one', 'two', 'three', ]:
                self.menu.addItem(
                    text=item,
                    onSelect=self.update_selection,
                    arguments=[
                        item,
                    ],
                )

    def initialize_menus(self):
        """
        HasMenus.initialize_menus

            Initialize the '_NMDisplay' and '_NMenuList' instance variables,
            which are used by the menu management classes.

        PopupSelect.initialize_menus

            Here we override the HasMenus.initialize_menus() method in order to
            disable the default '_MainMenu' and 'MENU_KEY' configuration.

        """
        if self.MENU_WIDTH:
            self._NMDisplay = self.MENU_DISPLAY_TYPE(columns=self.MENU_WIDTH)
        else:
            self._NMDisplay = self.MENU_DISPLAY_TYPE()
        if not hasattr(self, '_NMenuList'):
            self._NMenuList = []

    def display_menu(self, *args, **kwargs):
        self.popup_menu(self.menu)

    def update_selection(self, value):
        """
        This function updates the value of the widget, then exits the widget.
        The primary purpose of this method is to be called by the 'do()' method
        of a MenuItem object (via the 'onSelectFunction' MenuItem instance
        variable) contained in the 'menu' PopupSelect instance variable.
        """
        self.value = value
        self.h_exit_down(None)


if __name__ == '__main__':
    class TestForm(npyscreen.Form):
        def __init__(self, *args, **kwargs):
            npyscreen.Form.__init__(self, *args, **kwargs)

            self.add_handlers({
                "^Q": self.quit,
            })

        def quit(self, *args, **kwargs):
            self.parentApp.switchForm(None)

        def create(self):
            self.add_widget(
                PopupSelect,
                name="name",
                value="value",
            )

        def afterEditing(self):
            self.parentApp.setNextForm(None)

    class TestApplication(npyscreen.NPSAppManaged):
        def onStart(self):
            self.addForm('MAIN', TestForm)

    application = TestApplication()
    application.run()
