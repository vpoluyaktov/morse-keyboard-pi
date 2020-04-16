import npyscreen

class TextfieldNumbersOnly(npyscreen.Textfield):
    def __init__(self, *args, **keywords):
        self.IntLength = int(keywords['width']) - 1
        super(TextfieldNumbersOnly, self).__init__(*args, **keywords)

    def h_addch(self, inp):
         if chr(inp) in '1234567890-' and len(self.value) <= (self.IntLength -1):
            super(TextfieldNumbersOnly, self).h_addch(inp)

class TitleTextfieldNumbersOnly(npyscreen.TitleText):
    _entry_type = TextfieldNumbersOnly
