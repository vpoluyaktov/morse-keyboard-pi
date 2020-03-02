import npyscreen

from UI.ReceiverPager import ReceiverPager

class MainForm(npyscreen.FormWithMenus):
    receiverBox = None
    senderBox = None

    def create(self):
        super(MainForm, self).create()
        self.name = "CW Station v.0.0.1"

        # NewMenu.addItem(text = '', onSelect = function, shortcut = None, arguments = None, keywords = None)

        self.receiverBox = self.add(ReceiverPager, name = "Receiver", footer = "Received text", relx = 30,
                                    rely = 1, height = 5, max_width = 100, max_height = 10, scroll_exit = False,
                                    contained_widget_arguments = {"maxlen" : 4}
        )


        self.senderBox = self.add(npyscreen.BoxTitle, name = "Send", relx = 30, height = 5, max_height = 10,
                                  scroll_exit = False)

        self.receiverBox.entry_widget.buffer([], scroll_end=True, scroll_if_editing=False)

        self.receiverStarButton = self.add(npyscreen.ButtonPress, name = "Start", relx = 150, rely =2)


    def afterEditing(self):
        self.parentApp.setNextForm(None)

    def while_waiting(self):
        start_display_at = len(self.receiverBox.values) - self.receiverBox.height
        #self.receiverBox.entry_widget.start_display_at = start_display_at

