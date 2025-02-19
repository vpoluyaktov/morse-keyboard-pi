import npyscreen
import textwrap
from ui.box_title_color import BoxTitleColor

class SenderBox(BoxTitleColor):

    _contained_widget = npyscreen.MultiLineEdit

    def clear_text(self):   
        self.entry_widget.value = ""
        self.entry_widget.display()


    def add_text(self, text):
        buffer = self.entry_widget.values
        buffer_string = "".join(buffer)
        buffer_string += text
        wrapper = textwrap.TextWrapper(
            width=self.entry_widget.width - 1,
            replace_whitespace=False,
            drop_whitespace=False,
            break_long_words=False
        )
        values = wrapper.wrap(text=buffer_string)
        self.entry_widget.values = values
        self.entry_widget.buffer(
            [], scroll_end=True, scroll_if_editing=False)
        self.entry_widget.display()    


    def get_text(self):
        return self.entry_widget.value
