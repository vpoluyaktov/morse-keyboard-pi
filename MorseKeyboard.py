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


class App(npyscreen.NPSApp):

    # def onStart(self):
    #    self.add(npyscreen.TitleText, name = "Text:", value= "Hellow World!" ) 

    mainForm = None

    def _get_theme(self):
        return BlueTheme

    def draw(self):

        mainForm = self.WindowForm(parentApp=self)
        mainForm.add(npyscreen.BoxTitle, "Test" )
        mainForm.edit()

    def while_waiting(self):

        currentDT = datetime.datetime.now()
        str(currentDT)
        self.mainForm.receiverBox.values = ["Time: ", str(currentDT)]


if __name__ == "__main__":
    app = App()
    app.run()

