#!/usr/bin/python3

# import libs
try:
    from utils.tone_sound import ToneSound
    from array import array
    from queue import Queue
    import threading
    import time


except ImportError as error:
    print("You have to install some extras in order to use this shell script:")
    print(error)
    exit(1)    


class KeyboardTransmitter:

    transmitted_text = ""
    tranmitter_is_started = False
    sounder = None

    def __init__(self):
        # self.sounder = ToneSound()
         # init transmit queue
        self.keyboard_transmit_queue = Queue(maxsize=10000)
        
    def start_transmitter(self):
        self.stop_is_requested = False
        self.keyboard_transmitter_thread = threading.Thread(target=self.process_queue, args=(
            self.keyboard_transmit_queue,), daemon=True)
        self.keyboard_transmitter_thread.start()
        self.tranmitter_is_started = True

    def stop_transmitter(self):
        self.stop_is_requested = True            

    def transmit(self, text_to_transmit):

        if not self.tranmitter_is_started:
            self.start_transmitter()

        text_to_transmit = str.upper(text_to_transmit)

        for char in text_to_transmit:
            self.keyboard_transmit_queue.put(char)
        self.keyboard_transmit_queue.put("<BT>\n")

    def process_queue(self, keyboard_transmit_queue):
        
        while not self.stop_is_requested:
            char = keyboard_transmit_queue.get()  
            if char != '':
                self.char_to_morse(char)
                self.transmitted_text += char

        self.tranmitter_is_started = False    
             
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
        #self.sounder.start_beep()
        #time.sleep(50/1000)
        #self.sounder.stop_beep()
        time.sleep(1)







