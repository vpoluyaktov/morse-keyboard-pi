#!/usr/bin/env python
# encoding: utf-8


try:
    import npyscreen
    import pyaudio

    from sys import byteorder
    from array import array
    from struct import pack

    import pyaudio
    import wave
    import struct
    import numpy

    import datetime

except ImportError as error:
    print("You have to install some extras in order to use this shell script:")
    print(error)
    exit(1)

from UI.themes.BlueTheme import BlueTheme
from UI.MainForm import MainForm


class App(npyscreen.NPSAppManaged):

    # def onStart(self):
    #    self.add(npyscreen.TitleText, name = "Text:", value= "Hellow World!" ) 

    mainForm = None

    def onStart(self):
        #npyscreen.setTheme(BlueTheme)
        self.keypress_timeout_default = 1
        self.mainForm = self.addForm("MAIN", MainForm)
        self.mainForm.edit()

    def while_waiting(self):

        currentDT = datetime.datetime.now()
        self.mainForm.receiverBox.entry_widget.buffer([str(currentDT)], scroll_end=True, scroll_if_editing=False)
        self.mainForm.receiverBox.entry_widget.display()


if __name__ == "__main__":
    app = App()
    app.run()

