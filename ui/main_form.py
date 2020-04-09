import npyscreen

import threading
from queue import Queue
import curses
import time
from datetime import datetime

from receiver.listener import MorseListener
from receiver.decoder import MorseDecoder
from ui.log_pager import LogPager
from ui.sender_multiline_edit import SenderBox
from ui.box_title_color import BoxTitleColor
from transmitter.keyboard_transmitter import KeyboardTransmitter


class MainForm(npyscreen.FormWithMenus):
    receiver_control_box = None
    log_box = None
    sender_queue_box = None
    morse_listener = None
    morse_decoder = None
    listener_thread = None
    decoder_thread = None
    receiver_is_running = False
    is_transmitting = False

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
        self.add_log_box()
        self.add_sender_queue_box()
        self.add_transmit_box()
        self.add_shortcut_box()

        # init decoder queue
        self.morse_decoder_queue = Queue(maxsize=1000)

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

        self.receiver_save_log_button = self.add(
            npyscreen.ButtonPress, name="[ Save log         ]", relx=self.receiver_control_box.relx + 1)

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
        self.receiver_save_log_button.whenPressed = self.communication_log_save
        self.receiver_clear_button.whenPressed = self.communication_log_clear
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

    def add_log_box(self):
        # Log Box
        self.log_box = self.add(LogPager, name="Communication log", footer="Communication log",
                                relx=self.receiver_control_box.relx + self.receiver_control_box.width + 2,
                                rely=self.receiver_control_box.rely, max_height=int(self.lines/2 - 1), scroll_exit=True,
                                contained_widget_arguments={"maxlen": 10}
                                )
        self.log_box.entry_widget.buffer(
            [], scroll_end=True, scroll_if_editing=False)

    def add_sender_queue_box(self):
        # Sender Queue Box
        self.sender_queue_box = self.add(SenderBox, name="Sender queue",
                                         relx=self.receiver_control_box.relx + self.receiver_control_box.width + 2,
                                         max_height=int(self.lines/4 - 5) + 1,
                                         width=int(
                                             self.columns - self.receiver_control_box.relx - self.receiver_control_box.width - 24),
                                         editable=False, scroll_exit=False,
                                         )

        self.sender_queue_control_box = self.add(BoxTitleColor, name=None,
                                                 relx=self.sender_queue_box.relx + self.sender_queue_box.width + 1,
                                                 rely=self.sender_queue_box.rely,
                                                 max_height=self.sender_queue_box.height,
                                                 scroll_exit=True, editable=False)

        self.send_pause_resume_button = self.add(
            npyscreen.ButtonPress, name="[ Pause    ]",
            relx=self.sender_queue_control_box.relx + 1,
            rely=self.sender_queue_control_box.rely + 1)
        self.clear_sender_queue_button = self.add(
            npyscreen.ButtonPress, name="[ Clear    ]",
            relx=self.sender_queue_control_box.relx + 1,
            rely=self.sender_queue_control_box.rely + 2)

    def add_transmit_box(self):
        # Transmit
        self.to_transmit_box = self.add(SenderBox, name="Text to transmit",
                                        relx=self.receiver_control_box.relx + self.receiver_control_box.width + 2,
                                        rely=self.sender_queue_box.rely + self.sender_queue_box.height,
                                        max_height=int(self.lines/4 - 2),
                                        width=int(
                                            self.columns - self.receiver_control_box.relx - self.receiver_control_box.width - 24),
                                        editable=True, scroll_exit=False,
                                        )
        

        self.transmit_control_box = self.add(BoxTitleColor, name=None,
                                             relx=self.to_transmit_box.relx + self.sender_queue_box.width + 1,
                                             rely=self.to_transmit_box.rely,
                                             height=self.to_transmit_box.height,
                                             scroll_exit=True, editable=False)

        self.send_transmit_text_button = self.add(
            npyscreen.ButtonPress, name="[ Transmit ]",
            relx=self.transmit_control_box.relx + 1,
            rely=self.transmit_control_box.rely + 1)
        self.send_transmit_text_button.whenPressed = self.transmit_text

    def add_shortcut_box(self):
        # Shortcut Controls
        self.shortcut_control_box = self.add(BoxTitleColor, name="Shortcuts",
                                             relx=self.receiver_control_box.relx + self.receiver_control_box.width + 2,
                                             rely=self.to_transmit_box.rely + self.to_transmit_box.height,
                                             max_height=4,
                                             scroll_exit=True, editable=False)

        self.shortcut_cq_button = self.add(
            npyscreen.ButtonPress, name="[ CQ ]", relx=self.shortcut_control_box.relx + 1,
            rely=self.shortcut_control_box.rely + 1)

        self.shortcut_dx_button = self.add(
            npyscreen.ButtonPress, name="[ DX ]", relx=self.shortcut_cq_button.relx + self.shortcut_cq_button.width + 1,
            rely=self.shortcut_control_box.rely + 1)

        self.shortcut_callsing_button = self.add(
            npyscreen.ButtonPress, name="[ Call Sing ]", relx=self.shortcut_dx_button.relx + self.shortcut_dx_button.width + 1,
            rely=self.shortcut_control_box.rely + 1)

    def receiver_start_stop(self):
        if self.receiver_is_running:
            self.stop_receiver()
        elif self.receiver_select_device.value != None:
            self.start_receiver()
        else:
            npyscreen.notify("You need to select audio device first",
                             title="Error", form_color="CRITICAL")
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
            if self.is_transmitting:
                decoded_string = "---\n" + decoded_string    
            self.is_transmitting = False
            self.log_box.add_text(decoded_string)
        transmitted_text = self.keyboard_transmitter.get_transmitted_text()
        if transmitted_text != "":
            self.is_receiving = False
            if not self.is_transmitting:
                transmitted_text = "---\n" + transmitted_text  
                self.is_transmitting = True  
            self.log_box.add_text(transmitted_text)


        frequency = self.morse_decoder.get_frequency()
        wpm = self.morse_decoder.get_wpm()
        sound_level = self.morse_decoder.get_sound_level()

        self.level_autotune_checkbox.value = self.morse_decoder.sound_level_autotune
        self.level_autotune_checkbox.display()
        #if self.morse_decoder.sound_level_autotune:
        if not self.level_field.editing:
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

        commumication_box_header = "Communication log " + \
            u'\u2500' * int(self.log_box.width - 86)
        morse_ascii_history_length = self.log_box.width - \
            len(commumication_box_header) - 14
        morse_ascii_history = morse_ascii_history[-morse_ascii_history_length:]

        commumication_box_header += " [ {:" + \
            str(morse_ascii_history_length) + "s}] "
        self.log_box.name = commumication_box_header.format(
            morse_ascii_history)

        receiver_box_footer = "[ Queue: {:3d} | Speed: {:s} wpm | Level: {:4d} | Freq: {:3.0f} KHz ]"
        self.log_box.footer = receiver_box_footer.format(
            self.morse_decoder_queue.qsize(), wpm, sound_level, frequency)

        sender_queue = self.keyboard_transmitter.get_sender_queue()
        self.sender_queue_box.value = sender_queue    

        self.log_box.display()
        self.sender_queue_box.display()

    def transmit_text(self):
        text_to_transmit = self.to_transmit_box.get_text()
        self.keyboard_transmitter.transmit(text_to_transmit)
        self.to_transmit_box.clear_text()

    def toggle_level_autotune(self):
        self.morse_decoder.sound_level_autotune = self.level_autotune_checkbox.value
        if self.level_autotune_checkbox.value: 
            npyscreen.notify("Enabling Sound Level autotuning may lead to many low level false detections",
                             title="Warning", form_color="WARNING")
            time.sleep(4)


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

    def communication_log_save(self):
        file_name = datetime.now().strftime("%Y-%m-%d_%H:%M:%S") + ".log"
        f = open(file_name, 'w')
        f.write(self.log_box.get_text())
        f.close()

    def communication_log_clear(self):
        self.log_box.clear_text()
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
