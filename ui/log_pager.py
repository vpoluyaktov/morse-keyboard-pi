import npyscreen
import textwrap
from ui.box_title_color import BoxTitleColor
from utils.config import Config

class LogPager(BoxTitleColor):

    _contained_widget = npyscreen.BufferPager
    
    config = Config()
    
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
        while buffer_string[0] == self.config.MESSAGE_SEPARATOR:
            buffer_string = buffer_string[1:] 
        lines = buffer_string.split(self.config.MESSAGE_SEPARATOR)

        values = []
        for line in lines:
            if line != '':                
                values.extend(self.wrapper.wrap(line))
                if line != lines[-1]:
                    values.append(self.config.MESSAGE_SEPARATOR)
        self.entry_widget.values = values
        self.entry_widget.buffer(
            [], scroll_end=True, scroll_if_editing=False)
        self.entry_widget.display()


    def get_text(self):
        buffer = self.entry_widget.values
        buffer_string = "".join(buffer)
        return buffer_string

    def clear_text(self):
        self.entry_widget.values = []
        self.entry_widget.buffer([], scroll_end=True, scroll_if_editing=True)
        self.entry_widget.display()
