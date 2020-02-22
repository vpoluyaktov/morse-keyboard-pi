#!/usr/bin/env python
# encoding: utf-8

import npyscreen
from themes.BlueTheme import BlueTheme
from MainForm import MainForm

class App(npyscreen.NPSAppManaged):

    #def onStart(self):
    #    self.add(npyscreen.TitleText, name = "Text:", value= "Hellow World!" ) 

    def main(self):
        npyscreen.setTheme(BlueTheme)
        mainForm = self.addForm("MAIN", MainForm)
        mainForm.edit()

        
if __name__ == "__main__":
    app = App()
    app.run()   
