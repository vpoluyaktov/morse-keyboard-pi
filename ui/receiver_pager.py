import npyscreen
import textwrap
from ui.box_title_color import BoxTitleColor


class ReceiverPager(BoxTitleColor):

    _contained_widget = npyscreen.BufferPager
    
    def add_text(self, text):

        self.wrapper = textwrap.TextWrapper(
            width=self.entry_widget.width - 1,
            replace_whitespace=False,
            drop_whitespace=False,
            break_long_words=False
        )

        buffer = self.entry_widget.values
        buffer_string = "".join(buffer)
        buffer_string += text
        while buffer_string[0] == "---\n":
            buffer_string = buffer_string[1:] 
        lines = buffer_string.split("---\n")

        values = []
        for line in lines:
            if line != '':                
                values.extend(self.wrapper.wrap(line))
                if line != lines[-1]:
                    values.append("---\n")
        self.entry_widget.values = values
        self.entry_widget.buffer(
            [], scroll_end=True, scroll_if_editing=False)
        self.entry_widget.display()

    def clear_text(self):
        self.entry_widget.values = []
        self.entry_widget.buffer([], scroll_end=True, scroll_if_editing=True)
        self.entry_widget.display()
