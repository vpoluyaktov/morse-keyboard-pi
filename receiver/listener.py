#!/usr/bin/python3

try:

    from os import environ
    from sys import byteorder
    from array import array
    from struct import pack
    from collections import Counter
    from queue import Queue

    import pyaudio
    import wave
    import struct
    import numpy

except ImportError as error:
    print("You have to install some extras in order to use this shell script:")
    print(error)
    exit(1)


class MorseListener:

    DEVICE_INDEX = 2

    RATE = 44100  # frames per a second
    CHUNK_LENGTH_MS = 10
    FORMAT = pyaudio.paInt16
    ALLOWANCE = 3

    chunk = int(RATE / 1000 * CHUNK_LENGTH_MS)

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

                device_list.append([
                    "Index {i}: {name} (Max Channels {input_chn}, Default @ {rate} Hz)".format(i = i, name = name,
                        input_chn = input_chn, rate = int(rate))])

        return device_list

    def listen(self, morse_decoder_queue):

        p = pyaudio.PyAudio()

        stream = p.open(format = self.FORMAT, channels = 1, rate = self.RATE, input = True,
                        input_device_index = self.DEVICE_INDEX, frames_per_buffer = self.chunk)

        while True:
            sound_data = stream.read(self.chunk, exception_on_overflow = False)
            morse_decoder_queue.put(sound_data)

