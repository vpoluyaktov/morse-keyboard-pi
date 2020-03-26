#!/usr/bin/python3

from utils.tone_sound import ToneSound


try:
    from array import array
    from queue import Queue

except ImportError as error:
    print("You have to install some extras in order to use this shell script:")
    print(error)
    exit(1)    



class KeyboardTransmitter:

    def __init__(self, ):
        sounder = ToneSound()

    def transmit(self, keyboard_transmit_queue):
        self.stop_is_requested = False
        
        while not self.stop_is_requested:
            transmit_string = keyboard_transmit_queue.get()

            for char in transmit_string:
                None





