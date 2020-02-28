#!/usr/bin/python3

try:
    import pyaudio

    from sys import byteorder
    from array import array
    from struct import pack

    import pyaudio
    import wave
    import struct
    import numpy

except ImportError as error:
    print("You have to install some extras in order to use this shell script:")
    print(error)
    exit(1)

DEVICE_INDEX = 2

WPS = 20
WPS_VARIANCE = 20  # 10 persents
FREQ = 650
HzVARIANCE = 20
THRESHOLD = 300

RATE = 48000  # frames per a second
CHUNK_LENGTH_MS = 5
FORMAT = pyaudio.paInt16
ALLOWANCE = 3

chunk = int(RATE / 1000 * CHUNK_LENGTH_MS)
window = numpy.blackman(chunk)

# morse code timing
dit_length_ms = int(1200 / WPS)
dah_length_ms = dit_length_ms * 3
char_space_length_ms = dit_length_ms
letter_space_length_ms = dit_length_ms * 3
word_space_length_ms = dit_length_ms * 7

# morse code timing variances in frames
dit_length_min = int(dit_length_ms * ((100 - WPS_VARIANCE) / 100) / CHUNK_LENGTH_MS)
dit_length_max = int(dit_length_ms * ((100 + WPS_VARIANCE) / 100) / CHUNK_LENGTH_MS)
dah_length_min = dit_length_min * 3
dah_length_max = dit_length_max * 3
char_space_length_min = dit_length_min
char_space_length_max = dit_length_max
letter_space_length_min = dit_length_min * 3
letter_space_length_max = dit_length_max * 3
word_space_length_min = dit_length_min * 7
word_space_length_max = dit_length_max * 7

print("dit: ", dit_length_ms, "ms ", dit_length_min, "-", dit_length_max)
print("dah: ", dah_length_ms, "ms ", dah_length_min, "-", dah_length_max)
print("char: ", char_space_length_min, "-", char_space_length_max)
print("letter: ", letter_space_length_min, "-", letter_space_length_max)
print("word: ", word_space_length_min, "-", word_space_length_max)

WINDOW = letter_space_length_min  # process letter by letter

letter_to_morse = {"A": ".-", "B": "-...", "C": "-.-.", "D": "-..", "E": ".", "F": "..-.", "G": "--.", "H": "....",
    "I": "..", "J": ".---", "K": "-.-", "L": ".-..", "M": "--", "N": "-.", "O": "---", "P": ".--.", "Q": "--.-",
    "R": ".-.", "S": "...", "T": "-", "U": "..-", "V": "...-", "W": ".--", "X": "-..-", "Y": "-.--", "Z": "--..",
    "1": ".----", "2": "..---", "3": "...--", "4": "....-", "5": ".....", "6": "-....", "7": "--...", "8": "---..",
    "9": "----.", "0": "-----", "?": "..--..", ".": ".-.-.-", ",": "--..--", "!": "-.-.--", "'": ".----."}


def list_devices():
    """List all available microphone devices."""

    print("List of all available microphone devices:")
    pa = pyaudio.PyAudio()
    for i in range(pa.get_device_count()):
        dev = pa.get_device_info_by_index(i)
        input_chn = dev.get('maxInputChannels', 0)
        if input_chn > 0:
            name = dev.get('name')
            rate = dev.get('defaultSampleRate')
            print("Index {i}: {name} (Max Channels {input_chn}, Default @ {rate} Hz)".format(
                i=i, name=name, input_chn=input_chn, rate=int(rate)

            ))
    return 0


def is_silent(snd_data):
    "Returns 'True' if below the 'silent' threshold"
    return max(snd_data) < THRESHOLD


def normalize(snd_data):
    "Average the volume out"
    # 32768 maximum /2
    MAXIMUM = 16384
    times = float(MAXIMUM) / max(abs(i) for i in snd_data)

    r = array('h')
    for i in snd_data:
        r.append(int(i * times))
    return r


def record():
    sound_started = False
    syncronized = False
    num_silent = 0
    sound_sequence = ""

    print("Listening device #", DEVICE_INDEX)
    p = pyaudio.PyAudio()
    stream = p.open(format = FORMAT, channels = 1, rate = RATE, input = True, input_device_index = DEVICE_INDEX,
                    frames_per_buffer = chunk)

    # r = array('h')
    print("started")
    while True:

        snd_data = stream.read(chunk, exception_on_overflow = False)

        if byteorder == 'big':
            snd_data.byteswap()

        # r.extend(snd_data)
        sample_width = p.get_sample_size(FORMAT)

        # find frequency of each chunk
        indata = numpy.array(wave.struct.unpack("%dh" % (chunk), snd_data)) * window

        # take fft and square each value
        fftData = abs(numpy.fft.rfft(indata)) ** 2

        # find the maximum
        which = fftData[1:].argmax() + 1
        silent = is_silent(indata)

        if silent:
            thefreq = 0
        elif which != len(fftData) - 1:
            y0, y1, y2 = numpy.log(fftData[which - 1:which + 2:])
            x1 = (y2 - y0) * .5 / (2 * y1 - y2 - y0)
            # find the frequency and output it
            thefreq = (which + x1) * RATE / chunk
        else:
            thefreq = which * RATE / chunk
        # print(thefreq)

        if thefreq > (FREQ - HzVARIANCE) and thefreq < (FREQ + HzVARIANCE):
            # check if this is a new character started
            if num_silent >= letter_space_length_min and sound_started and syncronized:
                decode(sound_sequence)
                num_silent = 0
                sound_sequence = ""

            if syncronized:
                sound_sequence += "1"
            num_silent = 0
            sound_started = True
        elif sound_started:
            num_silent += 1
            if syncronized:
                sound_sequence += "0"
        else:
            # waiting for long selence so don't break a word
            num_silent += 1

        if num_silent >= word_space_length_min and sound_started:
            if sound_started and syncronized:
                decode(sound_sequence)
            num_silent = 0
            sound_sequence = ""
            sound_started = False
            syncronized = True

    print("ended")
    p.terminate()


def decode(list):
    # print(list)

    line_breakers = ".?!"

    list = list.split("0")
    listascii = ""
    counter = 0

    for i in range(len(list)):
        if len(list[i]) == 0:  # blank character adds 1
            counter += 1
        else:
            if counter < ALLOWANCE:
                list[i] += list[i - counter - 1]
                list[i - counter - 1] = ""
            counter = 0

    for i in range(len(list)):
        # print(len(list[i]), dit_length_min, dit_length_max)
        if len(list[i]) >= dit_length_min and len(list[i]) <= dit_length_max:
            listascii += "."
            counter = 0
        elif len(list[i]) >= dah_length_min and len(list[i]) <= dah_length_max:
            listascii += "-"
            counter = 0
        elif len(list[i]) == 0:  # blank character adds 1
            counter += 1
            if counter >= word_space_length_min:
                listascii += " "
                counter = 0

    listascii = listascii.split(" ")
    stringout = ""
    for i in range(len(listascii)):
        if listascii[i] == "":
            if not last_character in line_breakers:
              stringout += " "  # drop space in the beginning of a line
        else:
            letter_found = False
            last_character = None
            for letter, morse in letter_to_morse.items():
                if listascii[i] == morse:
                    stringout += letter
                    last_character = letter
                    letter_found = True
            if not letter_found:
                stringout += "_"
            if last_character in line_breakers:
                stringout += "\n"

    print(stringout, end = '', flush = True)


#    print(list)
#    print(listascii)

if __name__ == "__main__":
    list_devices()
    record()
