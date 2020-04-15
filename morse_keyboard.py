#!/usr/bin/env python
# encoding: utf-8

# check dependencies
try:
    import array
    import collections
    import curses
    import datetime
    import logging
    import matplotlib.pyplot as plt
    import npyscreen
    import numpy
    import os
    import pyaudio
    import queue
    import struct
    import struct
    import sys
    import textwrap
    import threading
    import time
    import time
    import warnings
    import wave

except ImportError as error:
    print("You have to install some extras in order to use this shell script:")
    print(error)
    exit(1)


from ui.themes.BlueTheme import BlueTheme
from ui.themes.WhiteTheme import WhiteTheme
from ui.main_form import MainForm

class App(npyscreen.NPSAppManaged):

    # create logger
    logger = logging.getLogger('CWStation')
    logger.setLevel(logging.DEBUG)
    fh = logging.FileHandler('cwstation.log')
    fh.setLevel(logging.DEBUG)
    ch = logging.StreamHandler()
    ch.setLevel(logging.ERROR)
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    fh.setFormatter(formatter)
    ch.setFormatter(formatter)
    logger.addHandler(fh)
    logger.addHandler(ch)

    main_form = None

    def onStart(self):
        npyscreen.setTheme(BlueTheme)
        #npyscreen.setTheme(npyscreen.Themes.BlackOnWhiteTheme)
        #npyscreen.setTheme(npyscreen.Themes.DefaultTheme)
        self.keypress_timeout_default = 1
        self.main_form = self.addForm("MAIN", MainForm)
        self.main_form.edit()

        logger = logging.getLogger('CWStation')
        logger.warning('CW Station started: %s', datetime.datetime.now())

    def while_waiting(self):
        None


if __name__ == "__main__":
    app = App()
    app.run()
