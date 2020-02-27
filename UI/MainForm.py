import npyscreen

class MainForm(npyscreen.FormWithMenus):

    receiverBox = None
    senderBox = None

    def create(self):
        super(MainForm, self).create()
        self.name = "CW Workstation v.0.0.1"

        #NewMenu.addItem(text = '', onSelect = function, shortcut = None, arguments = None, keywords = None)


        receiverBox = self.add(npyscreen.BoxTitle, name = "Receiver", footer = "Received text",
                               relx = 30, rely = 1, height = 5, max_width = 100, max_height = 10
                               )

        senderBox = self.add(npyscreen.BoxTitle, name = "Send",
                               relx = 30, height = 5, max_height = 10, scroll_exit = True
                             )

        receiverBox.entry_widget.scroll_exit = True
        receiverBox.values = ["Hello"]

        # ml = receiverBox.add(npyscreen.MultiLineEdit,
        #        value = """try typing here!\nMutiline text, press ^R to reformat.\n"""
        #       )

  #      receiverBox._contained_widget = ml

    def afterEditing(self):
        self.parentApp.setNextForm(None)


