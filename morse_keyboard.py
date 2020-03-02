#!/usr/bin/env python
# encoding: utf-8

try:
    import npyscreen

except ImportError as error:
    print("You have to install some extras in order to use this shell script:")
    print(error)
    exit(1)

from ui.themes.BlueTheme import BlueTheme
from ui.main_form import MainForm

class App(npyscreen.NPSAppManaged):


    main_form = None

    def onStart(self):
        # npyscreen.setTheme(BlueTheme)
        self.keypress_timeout_default = 1
        self.main_form = self.addForm("MAIN", MainForm)
        self.main_form.edit()

    def while_waiting(self):
        None

if __name__ == "__main__":
    app = App()
    app.run()

