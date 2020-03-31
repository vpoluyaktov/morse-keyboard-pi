import npyscreen

import threading
from queue import Queue
import curses
import time

from receiver.listener import MorseListener
from receiver.decoder import MorseDecoder
from ui.receiver_pager import ReceiverPager
from ui.sender_multiline_edit import SenderBox
from ui.box_title_color import BoxTitleColor
from transmitter.keyboard_transmitter import KeyboardTransmitter


class MainForm(npyscreen.FormWithMenus):
    receiver_control_box = None
    receiver_box = None
    sender_box = None
    morse_listener = None
    morse_decoder = None
    listener_thread = None
    decoder_thread = None
    receiver_is_running = False

    def create(self):
        super(MainForm, self).create()
        self.name = "CW Station v.0.0.1"

        self.morse_listener = MorseListener()
        self.morse_decoder = MorseDecoder()
        self.keyboard_transmitter = KeyboardTransmitter()

        # main_menu = npyscreen.MenuDisplayScreen.addItem(text = 'Device', onSelect = self.receiver_select_device, shortcut = None, arguments = None, keywords = None)

        # create screen controls
        self.add_receiver_device_control()
        self.add_receiver_controls_box()
        self.add_sender_contorls_box()
        self.add_receiver_log_box()
        self.add_sender_log_box()

        # init decoder queue
        self.morse_decoder_queue = Queue(maxsize=1000)

        # init transmit queue
        self.keyboard_transmit_queue = Queue(maxsize=1000)
        self.keyboard_transmit_queue.empty()
        self.keyboard_transmitter_thread = threading.Thread(target=self.keyboard_transmitter.transmit, args=(
            self.keyboard_transmit_queue,), daemon=True)
        self.keyboard_transmitter_thread.start()

    def afterEditing(self):
        self.parentApp.setNextForm(None)

    def add_receiver_device_control(self):
        self.receiver_select_device = self.add(
            npyscreen.TitleCombo,  name="Audio Device:", relx=8, rely=1,
            values=[el[1] for el in self.morse_listener.get_devices_list()])
        self.receiver_select_device.when_cursor_moved = self.receiver_refresh_device_list
        self.receiver_select_device.when_value_edited = self.receiver_change_device

    def add_receiver_controls_box(self):
        # Receiver Controls
        self.receiver_control_box = self.add(BoxTitleColor, name="Receiver Controls", relx=3, rely=2, width=26,
                                             max_height=int(self.lines/2 - 1), scroll_exit=True, editable=False)

        self.receiver_start_stop_button = self.add(
            npyscreen.ButtonPress, name="[ Start receiver   ]", relx=self.receiver_control_box.relx + 1,
            rely=self.receiver_control_box.rely + 1)

        self.receiver_clear_button = self.add(
            npyscreen.ButtonPress, name="[ Clear log        ]", relx=self.receiver_control_box.relx + 1)

        self.receiver_debug_button = self.add(
            npyscreen.ButtonPress, name="[ Debug plot       ]", relx=self.receiver_control_box.relx + 1)

        self.add(npyscreen.FixedText, value="~" * (self.receiver_control_box.width-2),
                 relx=self.receiver_control_box.relx + 1, editable=False)

        self.level_autotune_checkbox = self.add(
            npyscreen.CheckBox, name="Level Autotune", relx=self.receiver_control_box.relx + 3, width=21, highlight=True)

        self.level_field = self.add(
            npyscreen.TitleText, name="Threshold:", relx=self.receiver_control_box.relx + 3, begin_entry_at=16, field_width=23)

        self.add(npyscreen.FixedText, value="~" * (self.receiver_control_box.width-2),
                 relx=self.receiver_control_box.relx + 1, editable=False)

        self.freq_autotune_checkbox = self.add(
            npyscreen.CheckBox, name="Freq Autotune", relx=self.receiver_control_box.relx + 3, width=21, highlight=True)

        self.freq_field = self.add(
            npyscreen.TitleText, name="Frequency:", relx=self.receiver_control_box.relx + 3, begin_entry_at=17, field_width=23)

        self.add(npyscreen.FixedText, value="~" * (self.receiver_control_box.width-2),
                 relx=self.receiver_control_box.relx + 1, editable=False)

        self.wpm_autotune_checkbox = self.add(
            npyscreen.CheckBox, name="WPM Autotune", relx=self.receiver_control_box.relx + 3, width=21, highlight=True)

        self.wpm_field = self.add(
            npyscreen.TitleText, name="WPM:", relx=self.receiver_control_box.relx + 3, begin_entry_at=18, field_width=22)

        # Control bindings
        self.receiver_start_stop_button.whenPressed = self.receiver_start_stop
        self.receiver_clear_button.whenPressed = self.receiver_clear
        self.receiver_debug_button.whenPressed = self.morse_decoder.generate_plot
        self.level_autotune_checkbox.whenToggled = self.toggle_level_autotune
        self.level_field.when_value_edited = self.set_level
        self.freq_autotune_checkbox.whenToggled = self.toggle_freq_autotune
        self.freq_field.when_value_edited = self.set_freq
        self.wpm_autotune_checkbox.whenToggled = self.toggle_wpm_autotune
        self.wpm_field.when_value_edited = self.set_wpm


    def add_sender_contorls_box(self):
        # Sender Controls
        self.sender_control_box = self.add(BoxTitleColor, name="Sender Controls", relx=3,
                                           rely=self.receiver_control_box.rely + self.receiver_control_box.height, width=26,
                                           scroll_exit=True, editable=False)

    def add_receiver_log_box(self):
        # Receiver Box
        self.receiver_box = self.add(ReceiverPager, name="Receiver log", footer="Received text",
                                     relx=self.receiver_control_box.relx + self.receiver_control_box.width + 2,
                                     rely=self.receiver_control_box.rely, max_height=int(self.lines/2 - 1), scroll_exit=True,
                                     contained_widget_arguments={"maxlen": 10}
                                     )
        self.receiver_box.entry_widget.buffer(
            [], scroll_end=True, scroll_if_editing=False)                             

    def add_sender_log_box(self):
        # Sender Box
        self.sender_box = self.add(SenderBox, name="Sending log",
                                   relx=self.receiver_control_box.relx + self.receiver_control_box.width + 2,
                                   editable=True, scroll_exit=True,
                                   )
        self.sender_box.when_value_edited = self.transmit_keyboard_char                           

    def receiver_start_stop(self):
        if self.receiver_is_running:
            self.stop_receiver()
        elif self.receiver_select_device.value != None:
            self.start_receiver()
        else: 
            npyscreen.notify("You need to select audio device first", title="Error", form_color="CRITICAL")
            time.sleep(2) 

    def start_receiver(self):
        self.morse_decoder_queue.empty()
        self.listener_thread = threading.Thread(target=self.morse_listener.listen, args=(
            self.morse_decoder_queue,), daemon=True)
        self.decoder_thread = threading.Thread(target=self.morse_decoder.decode, args=(
            self.morse_decoder_queue,), daemon=True)
        self.listener_thread.start()
        self.decoder_thread.start()
        self.receiver_start_stop_button.name = "[ Stop receiver    ]"
        self.receiver_is_running = True

    def stop_receiver(self):
        self.morse_listener.stop()
        self.morse_decoder.stop()
        self.morse_decoder_queue.empty()
        self.receiver_start_stop_button.name = "[ Start receiver   ]"
        self.receiver_is_running = False

    def while_waiting(self):
        decoded_string = self.morse_decoder.get_buffer()
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

        receiver_box_header = "Receiver log " + \
            u'\u2500' * int(self.receiver_box.width - 86)
        morse_ascii_history_length = self.receiver_box.width - \
            len(receiver_box_header) - 14
        morse_ascii_history = morse_ascii_history[-morse_ascii_history_length:]

        receiver_box_header += " [ {:" + \
            str(morse_ascii_history_length) + "s}] "
        self.receiver_box.name = receiver_box_header.format(
            morse_ascii_history)

        receiver_box_footer = "[ Queue: {:3d} | Speed: {:s} wpm | Level: {:4d} | Freq: {:3.0f} KHz ]"
        self.receiver_box.footer = receiver_box_footer.format(
            self.morse_decoder_queue.qsize(), wpm, sound_level, frequency)

        self.receiver_box.display()

    def transmit_keyboard_char(self):
        char_to_transmit = self.sender_box.value
        self.keyboard_transmit_queue.put(char_to_transmit)

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

    def receiver_refresh_device_list(self):
        receiver_device_list = [
            el[1] for el in self.morse_listener.get_devices_list()]
        self.receiver_select_device.values = receiver_device_list


    def receiver_change_device(self):
        selected_choice = self.receiver_select_device.value
        if selected_choice != None:
            audio_device_list = self.morse_listener.get_devices_list()
            audio_device = audio_device_list[selected_choice]
            audio_device_index = audio_device[0]
            self.morse_listener.audio_device_index = audio_device_index
            if self.receiver_is_running:
                self.stop_receiver()
                time.sleep(1)
                self.start_receiver()
