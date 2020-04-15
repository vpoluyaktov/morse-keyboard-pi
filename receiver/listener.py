from os import environ
from sys import byteorder
from array import array
from struct import pack
from collections import Counter
from queue import Queue
import pyaudio
import wave
import struct
import numpy as np

from utils.config import Config


class MorseListener:

    config = Config()

    audio_device_index = 0
    stop_is_requested = False

    def stop(self):
        self.stop_is_requested = True

    def get_devices_list(self):
        # List all available microphone devices

        device_list = []
        pa = pyaudio.PyAudio()
        for i in range(pa.get_device_count()):
            dev = pa.get_device_info_by_index(i)
            input_chn = dev.get('maxInputChannels', 0)
            if input_chn > 0:
                name = dev.get('name')
                rate = dev.get('defaultSampleRate')

                device_list.append(
                    [i, "{index}: {name} (Max Channels {input_chn}, Default @ {rate} Hz)".format(index=i, name=name,
                                                                                                 input_chn=input_chn, rate=int(rate))])
        pa = None

        return device_list

    def listen(self, morse_decoder_queue):

        self.stop_is_requested = False

        p = pyaudio.PyAudio()

        stream = p.open(format=self.config.FORMAT, channels=1, rate=self.config.RATE, input=True,
                        input_device_index=self.audio_device_index, frames_per_buffer=self.config.chunk)

        while not self.stop_is_requested:
            sound_data = stream.read(self.config.chunk, exception_on_overflow=False)
            morse_decoder_queue.put(sound_data)

        return
