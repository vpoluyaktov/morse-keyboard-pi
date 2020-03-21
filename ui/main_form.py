import npyscreen

import threading
from queue import Queue

from receiver.listener import MorseListener
from receiver.decoder import MorseDecoder
from ui.receiver_pager import ReceiverPager


class MainForm(npyscreen.FormWithMenus):
    control_box = None
    receiver_box = None
    sender_box = None

    def create(self):
        super(MainForm, self).create()
        self.name = "CW Station v.0.0.1"
        # self.FIX_MINIMUM_SIZE_WHEN_CREATED = False

        # NewMenu.addItem(text = '', onSelect = function, shortcut = None, arguments = None, keywords = None)

        self.control_box = self.add(npyscreen.BoxTitle, name="Controls", relx=3, rely=1, width=25,
                                    scroll_exit=True, editable=False)

        self.receiver_start_stop_button = self.add(
            npyscreen.ButtonPress, name="[ Start/Stop ]", relx=self.control_box.relx + 1, rely=self.control_box.rely + 2)

        self.receiver_clear_button = self.add(
            npyscreen.ButtonPress, name="[ Clear      ]", relx=self.control_box.relx + 1)

        self.receiver_debug_button = self.add(
            npyscreen.ButtonPress, name="[ Debug plot ]", relx=self.control_box.relx + 1)

        self.receiver_box = self.add(ReceiverPager, name="Receiver", footer="Received text",
                                     relx=self.control_box.relx + self.control_box.width + 2, rely=1, max_height=int(self.lines/2 - 1), scroll_exit=True,
                                     contained_widget_arguments={"maxlen": 10}
                                     )

        self.sender_box = self.add(npyscreen.BoxTitle, name="Send",
                                   relx=self.control_box.relx + self.control_box.width + 2,
                                   scroll_exit=True)

        self.receiver_box.entry_widget.buffer(
            [], scroll_end=True, scroll_if_editing=False)

        self.morse_decoder_queue = Queue(maxsize=1000)

        self.morse_listener = MorseListener()
        self.morse_decoder = MorseDecoder()
        listener_thread = threading.Thread(target=self.morse_listener.listen, args=(
            self.morse_decoder_queue,), daemon=True)
        decoder_thread = threading.Thread(target=self.morse_decoder.decode, args=(
            self.morse_decoder_queue,), daemon=True)

        #self.receiver_box.entry_widget.values = self.morse_listener.get_devices_list()

        self.morse_decoder_queue.empty()
        listener_thread.start()
        decoder_thread.start()

        # self.receiver_start_stop_button.whenPressed = self.morse_decoder.start
        self.receiver_clear_button.whenPressed = self.receiver_box.clear_text
        self.receiver_debug_button.whenPressed = self.morse_decoder.generate_plot

    def afterEditing(self):
        self.parentApp.setNextForm(None)

    def while_waiting(self):

        decoded_string = self.morse_decoder.getBuffer()
        if decoded_string != "":
            self.receiver_box.add_text(decoded_string)

        frequency = self.morse_decoder.get_frequency()
        wpm = self.morse_decoder.get_wpm()
        sound_level = self.morse_decoder.get_sound_level()
        self.receiver_box.footer = "Queue: {:3d}    Speed: {:s} wpm    Level: {:4d}    Freq: {:3.0f} KHz"\
            .format(self.morse_decoder_queue.qsize(), wpm, sound_level, frequency)
        self.receiver_box.display()
