import npyscreen
import textwrap
import threading
from queue import Queue

from receiver.listener import MorseListener
from receiver.decoder import MorseDecoder
from ui.receiver_pager import ReceiverPager

class MainForm(npyscreen.FormWithMenus):
    receiver_box = None
    sender_box = None

    def create(self):
        super(MainForm, self).create()
        self.name = "CW Station v.0.0.1"

        # NewMenu.addItem(text = '', onSelect = function, shortcut = None, arguments = None, keywords = None)

        self.receiver_box = self.add(ReceiverPager, name = "Receiver", footer = "Received text", relx = 30,
                                     rely = 1, height = 5, max_width = 100, max_height = 10, scroll_exit = False,
                                     contained_widget_arguments = {"maxlen" : 4}
                                     )


        self.sender_box = self.add(npyscreen.BoxTitle, name = "Send", relx = 30, height = 5, max_height = 10,
                                   scroll_exit = False)

        self.receiver_box.entry_widget.buffer([], scroll_end=True, scroll_if_editing=False)

        self.receiver_star_button = self.add(npyscreen.ButtonPress, name = "Start", relx = 150, rely =2)


        self.morse_decoder_queue = Queue(maxsize = 1000)

        self.morse_listener = MorseListener()
        self.morse_decoder = MorseDecoder()
        listener_thread = threading.Thread(target = self.morse_listener.listen, args = (self.morse_decoder_queue,), daemon = True)
        decoder_thread = threading.Thread(target = self.morse_decoder.decode, args = (self.morse_decoder_queue,), daemon = True)

        #self.receiver_box.entry_widget.values = self.morse_listener.get_devices_list()

        self.morse_decoder_queue.empty()
        listener_thread.start()
        decoder_thread.start()


    def afterEditing(self):
        self.parentApp.setNextForm(None)


    def while_waiting(self):

        decoded_string = self.morse_decoder.getBuffer()
        if decoded_string != "" :
            buffer = self.receiver_box.entry_widget.values
            buffer_string = "".join(buffer)
            buffer_string += decoded_string
            wrapper = textwrap.TextWrapper(
                    width = self.receiver_box.entry_widget.width - 1,
                    replace_whitespace = False,
                    drop_whitespace = False,
                    break_long_words = False
                )
            values = wrapper.wrap(text=buffer_string)
            self.receiver_box.entry_widget.values = values
            self.receiver_box.entry_widget.buffer([], scroll_end=True, scroll_if_editing=False)
            self.receiver_box.entry_widget.display()

        frequency = self.morse_decoder.get_frequency()
        (dit_duration, dash_duration) = self.morse_decoder.get_wps()
        (sound_level, threshold) = self.morse_decoder.get_sound_level()
        self.receiver_box.footer = "Queue: {:3d} WSP: {:3d}/{:3d} Level: {:4d}/{:4d} Freq: {:3.0f} KHz"\
            .format(self.morse_decoder_queue.qsize(), dit_duration, dash_duration, sound_level, threshold, frequency)
        self.receiver_box.display()
