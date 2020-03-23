import npyscreen

import threading
from queue import Queue
import curses

from receiver.listener import MorseListener
from receiver.decoder import MorseDecoder
from ui.receiver_pager import ReceiverPager
from ui.box_title_color import BoxTitleColor


class MainForm(npyscreen.FormWithMenus):
    control_box = None
    receiver_box = None
    sender_box = None

    def create(self):
        super(MainForm, self).create()
        self.name = "CW Station v.0.0.1"

        # NewMenu.addItem(text = '', onSelect = function, shortcut = None, arguments = None, keywords = None)
        # Receiver Controls
        self.control_box = self.add(npyscreen.BoxTitle, name="Receiver Controls", relx=3, rely=1, width=26,
                                    scroll_exit=True, editable=False)

        self.receiver_start_stop_button = self.add(
            npyscreen.ButtonPress, name="[ Start/Stop ]", relx=self.control_box.relx + 1, rely=self.control_box.rely + 2)

        self.receiver_clear_button = self.add(
            npyscreen.ButtonPress, name="[ Clear      ]", relx=self.control_box.relx + 1)

        self.receiver_debug_button = self.add(
            npyscreen.ButtonPress, name="[ Debug plot ]", relx=self.control_box.relx + 1)

        self.add(npyscreen.FixedText, value="~" * (self.control_box.width-2),
                 relx=self.control_box.relx + 1, editable=False)

        self.level_autotune_checkbox = self.add(
            npyscreen.CheckBox, name="Level Autotune", relx=self.control_box.relx + 3, width=20, highlight=True)

        self.level_field = self.add(
            npyscreen.TitleText, name="Threshold:", relx=self.control_box.relx + 3, begin_entry_at=15, field_width=22)

        self.add(npyscreen.FixedText, value="~" * (self.control_box.width-2),
                 relx=self.control_box.relx + 1, editable=False)

        self.freq_autotune_checkbox = self.add(
            npyscreen.CheckBox, name="Freq Autotune", relx=self.control_box.relx + 3, width=20, highlight=True)

        self.freq_field = self.add(
            npyscreen.TitleText, name="Frequency:", relx=self.control_box.relx + 3, begin_entry_at=15, field_width=22)

        self.add(npyscreen.FixedText, value="~" * (self.control_box.width-2),
                 relx=self.control_box.relx + 1, editable=False)

        self.wpm_autotune_checkbox = self.add(
            npyscreen.CheckBox, name="WPM Autotune", relx=self.control_box.relx + 3, width=20, highlight=True)

        self.wpm_field = self.add(
            npyscreen.TitleText, name="WPM:", relx=self.control_box.relx + 3, begin_entry_at=15, field_width=19)

        # Receiver Box
        self.receiver_box = self.add(ReceiverPager, name="Receiver log", footer="Received text",
                                     relx=self.control_box.relx + self.control_box.width + 2, rely=1, max_height=int(self.lines/2 - 1), scroll_exit=True,
                                     contained_widget_arguments={"maxlen": 10}
                                     )
        # Sender Box
        self.sender_box = self.add(BoxTitleColor, name="Sending log",
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

        # self.receiver_box.entry_widget.values = self.morse_listener.get_devices_list()

        self.morse_decoder_queue.empty()
        listener_thread.start()
        decoder_thread.start()

        # self.receiver_start_stop_button.whenPressed = self.morse_decoder.start
        self.receiver_clear_button.whenPressed = self.receiver_clear
        self.receiver_debug_button.whenPressed = self.morse_decoder.generate_plot

        self.level_autotune_checkbox.whenToggled = self.toggle_level_autotune
        self.level_field.when_value_edited = self.set_level
        self.freq_autotune_checkbox.whenToggled = self.toggle_freq_autotune
        self.freq_field.when_value_edited = self.set_freq
        self.wpm_autotune_checkbox.whenToggled = self.toggle_wpm_autotune
        self.wpm_field.when_value_edited = self.set_wpm

    def afterEditing(self):
        self.parentApp.setNextForm(None)

    def while_waiting(self):
        decoded_string = self.morse_decoder.getBuffer()
        if decoded_string != "":
            self.receiver_box.add_text(decoded_string)

        frequency = self.morse_decoder.get_frequency()
        wpm = self.morse_decoder.get_wpm()
        sound_level = self.morse_decoder.get_sound_level()

        self.level_autotune_checkbox.value = self.morse_decoder.sound_level_autotune
        self.level_autotune_checkbox.display()
        if self.morse_decoder.sound_level_autotune:
            self.level_field.value = str(
                self.morse_decoder.sound_level_threshold)
            self.level_field.display()

        self.freq_autotune_checkbox.value = self.morse_decoder.frequency_auto_tune
        self.freq_autotune_checkbox.display()
        if self.morse_decoder.frequency_auto_tune:
            self.freq_field.value = str(int(self.morse_decoder.frequency))
            self.freq_field.display()

        self.wpm_autotune_checkbox.value = self.morse_decoder.wpm_autotune
        self.wpm_autotune_checkbox.display()
        if self.morse_decoder.wpm_autotune:
            self.wpm_field.value = str(self.morse_decoder.wpm)
            self.wpm_field.display()

        morse_ascii_history = self.morse_decoder.get_morse_ascii_history()

        receiver_box_header = "Receiver log " + u'\u2500' * int(self.receiver_box.width * 1/3) + " "
        morse_ascii_history_length = self.receiver_box.width - \
            len(receiver_box_header) - 12
        morse_ascii_history = morse_ascii_history[-morse_ascii_history_length:]

        receiver_box_header += "[ {:" + \
            str(morse_ascii_history_length-4) + "s}]"
        self.receiver_box.name = receiver_box_header.format(
            morse_ascii_history)

        receiver_box_footer = "Queue: {:3d} | Speed: {:s} wpm | Level: {:4d} | Freq: {:3.0f} KHz"
        self.receiver_box.footer = receiver_box_footer.format(
            self.morse_decoder_queue.qsize(), wpm, sound_level, frequency)

        self.receiver_box.display()

    def toggle_level_autotune(self):
        self.morse_decoder.sound_level_autotune = self.level_autotune_checkbox.value

    def set_level(self):
        if self.level_field.value != "":
            self.morse_decoder.sound_level_threshold = int(
                self.level_field.value)

    def toggle_freq_autotune(self):
        self.morse_decoder.frequency_auto_tune = self.freq_autotune_checkbox.value

    def set_freq(self):
        if self.freq_field.value != "":
            self.morse_decoder.frequency = int(self.freq_field.value)

    def toggle_wpm_autotune(self):
        self.morse_decoder.wpm_autotune = self.wpm_autotune_checkbox.value

    def set_wpm(self):
        if self.wpm_field.value != "":
            self.morse_decoder.wpm = int(self.wpm_field.value)

    def receiver_clear(self):
        self.receiver_box.clear_text()
        self.morse_decoder.clear_morse_ascii_history()
