import npyscreen

class MainForm(npyscreen.SplitForm):

    def create(self):
        self.name = "Welcome to Npyscreen"
        t  = self.add(npyscreen.TitleText, name = "Text:", )
        fn = self.add(npyscreen.TitleFilename, name = "Filename:",)
        fn2 = self.add(npyscreen.TitleFilenameCombo, name="Filename2:")
        dt = self.add(npyscreen.TitleDateCombo, name = "Date:")
        s  = self.add(npyscreen.TitleSliderPercent, accuracy=0, out_of=12, name = "Slider")
        ml = self.add(npyscreen.MultiLineEdit,
               value = """try typing here!\nMutiline text, press ^R to reformat.\n""",
               max_height=5, rely=9)
        ms = self.add(npyscreen.TitleSelectOne, max_height=4, value = [1,], name="Pick One",
                values = ["Option1","Option2","Option3"], scroll_exit=True)
        ms2= self.add(npyscreen.TitleMultiSelect, max_height =-2, value = [1,], name="Pick Several",
                values = ["Option1","Option2","Option3"], scroll_exit=True)


    def afterEditing(self):
        self.parentApp.setNextForm(None)
