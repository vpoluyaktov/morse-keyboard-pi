from array import array
from queue import Queue
import threading
import time

from utils.morse_sound import MorseSound
from utils.morse_lookup import MorseLookup
from utils.config import Config

class KeyboardTransmitter:

    config = Config()

    transmitted_text = ""
    morse_ascii_history = ""
    tranmitter_is_started = False
    sounder = None

    def __init__(self):
        # init transmit queue
        self.keyboard_transmit_queue = Queue(self.config.keyboard_transmit_queue_maxsize)

    def start_transmitter(self):
        self.sounder = MorseSound(self.config)
        self.morse_lookup = MorseLookup()
        self.stop_is_requested = False
        self.keyboard_transmitter_thread = threading.Thread(target=self.process_queue, args=(
            self.keyboard_transmit_queue,), daemon=True)
        self.keyboard_transmitter_thread.start()
        self.tranmitter_is_started = True

    def stop_transmitter(self):
        self.stop_is_requested = True
        self.keyboard_transmit_queue.put('')
        # wait until the transmitter is really stopped
        while self.tranmitter_is_started:
            None

    def transmit(self, text_to_transmit):
        if not self.tranmitter_is_started:
            self.start_transmitter()
        text_to_transmit = str.upper(text_to_transmit)
        for char in text_to_transmit:
            self.keyboard_transmit_queue.put(char)
        self.keyboard_transmit_queue.put("<BT>")

    def process_queue(self, keyboard_transmit_queue):
        while not self.stop_is_requested:
            char = keyboard_transmit_queue.get()
            if char != '':
                self.char_to_morse(char)
                self.transmitted_text += char
        self.tranmitter_is_started = False
        self.sounder.destroy()

    def get_sender_queue(self):
        return ''.join(self.keyboard_transmit_queue.queue)

    def clear_sender_queue(self):
        self.keyboard_transmit_queue.queue.clear()
        None

    def get_transmitted_text(self):
        text = self.transmitted_text
        self.transmitted_text = ""
        return text

    def char_to_morse(self, char):
        morse_code = self.morse_lookup.get_code_by_char(char)
        if morse_code != "":
            self.morse_ascii_history += (morse_code + " ")
            self.sounder.play_morse_code(morse_code)

    def get_morse_ascii_history(self):
        return self.morse_ascii_history

    def clear_morse_ascii_history(self):
        self.morse_ascii_history = ""        
