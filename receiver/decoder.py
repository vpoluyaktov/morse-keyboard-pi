#!/usr/bin/python3

try:

    from sys import byteorder
    from array import array
    from struct import pack
    from collections import Counter
    import wave

    import numpy

except ImportError as error:
    print("You have to install some extras in order to use this shell script:")
    print(error)
    exit(1)


class MorseDecoder:
    output_buffer = ""

    THRESHOLD = 300

    WPS = 20
    WPS_VARIANCE = 20  # 10 persents

    FREQ = 650
    HzVARIANCE = 20
    frequency_auto_tune = True

    RATE = 44100  # frames per a second
    CHUNK_LENGTH_MS = 5
    ALLOWANCE = 3

    chunk = int(RATE / 1000 * CHUNK_LENGTH_MS)
    window = numpy.blackman(chunk)

    frequency_history = []
    beep_duration_history = []
    keep_frequency_sec = 5
    keep_number_of_chunks = int(1000 / CHUNK_LENGTH_MS * keep_frequency_sec)

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
                       "I": "..", "J": ".---", "K": "-.-", "L": ".-..", "M": "--", "N": "-.", "O": "---", "P": ".--.",
                       "Q": "--.-", "R": ".-.", "S": "...", "T": "-", "U": "..-", "V": "...-", "W": ".--", "X": "-..-",
                       "Y": "-.--", "Z": "--..", "1": ".----", "2": "..---", "3": "...--", "4": "....-", "5": ".....",
                       "6": "-....", "7": "--...", "8": "---..", "9": "----.", "0": "-----", "?": "..--..",
                       ".": ".-.-.-", ",": "--..--", "!": "-.-.--", "'": ".----."}

    def is_silent(self, snd_data):
        "Returns 'True' if below the 'silent' threshold"
        return max(snd_data) < self.THRESHOLD

    def normalize(self, snd_data):
        "Average the volume out"
        # 32768 maximum /2
        MAXIMUM = 16384
        times = float(MAXIMUM) / max(abs(i) for i in snd_data)

        r = ['h']
        for i in snd_data:
            r.append(int(i * times))
        return bytes(r, 'utf-8')

    def decode(self, morse_decoder_queue):
        sound_started = False
        syncronized = False
        num_silent = 0
        sound_sequence = ""

        while True:

            sound_data = morse_decoder_queue.get()

            if sound_data is None:
                break

            if byteorder == 'big':
                sound_data.byteswap()

            # snd_data = self.normalize(snd_data)

            # r.extend(snd_data)
            #sample_width = p.get_sample_size(self.FORMAT)

            # find frequency of each chunk
            indata = numpy.array(wave.struct.unpack("%dh" % (self.chunk), sound_data)) * self.window

            # take fft and square each value
            fftData = abs(numpy.fft.rfft(indata)) ** 2

            # find the maximum
            which = fftData[1:].argmax() + 1
            silent = self.is_silent(indata)

            if silent:
                frequency = 0
            elif which != len(fftData) - 1:
                y0, y1, y2 = numpy.log(fftData[which - 1:which + 2:])
                x1 = (y2 - y0) * .5 / (2 * y1 - y2 - y0)
                # find the frequency and output it
                frequency = (which + x1) * self.RATE / self.chunk
            else:
                frequency = which * self.RATE / self.chunk

            # keep last 5 sec of frequency measurements
            if frequency > 450 and frequency < 900:
                self.frequency_history.append(round(frequency, 0))
                self.frequency_history = self.frequency_history[-self.keep_number_of_chunks:]

            if frequency > (self.FREQ - self.HzVARIANCE) and frequency < (self.FREQ + self.HzVARIANCE):
                # check if this is a new character started
                if num_silent >= self.letter_space_length_min and sound_started and syncronized:
                    self.decode_sequence(sound_sequence)
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

            if num_silent >= self.word_space_length_min and sound_started:
                if sound_started and syncronized:
                    self.decode_sequence(sound_sequence)
                num_silent = 0
                sound_sequence = ""
                sound_started = False
                syncronized = True

    def decode_sequence(self, list):
        # print(list)

        line_breakers = ".?!"
        last_character = ""

        list = list.split("0")
        listascii = ""
        counter = 0

        for i in range(len(list)):
            if len(list[i]) == 0:  # blank character adds 1
                counter += 1
            else:
                if counter < self.ALLOWANCE:
                    list[i] += list[i - counter - 1]
                    list[i - counter - 1] = ""
                counter = 0

        for i in range(len(list)):
            if len(list[i]) > 0:
                self.beep_duration_history.append(len(list[i]))
                self.beep_duration_history = self.beep_duration_history[-self.keep_number_of_chunks:]

            # print(len(list[i]), dit_length_min, dit_length_max)
            if len(list[i]) >= self.dit_length_min and len(list[i]) <= self.dit_length_max:
                listascii += "."
                counter = 0
            elif len(list[i]) >= self.dah_length_min and len(list[i]) <= self.dah_length_max:
                listascii += "-"
                counter = 0
            elif len(list[i]) == 0:  # blank character adds 1
                counter += 1
                if counter >= self.word_space_length_min:
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
                for letter, morse in self.letter_to_morse.items():
                    if listascii[i] == morse:
                        stringout += letter
                        last_character = letter
                        letter_found = True
                if not letter_found:
                    last_character = "_"
                    stringout += last_character
                if last_character in line_breakers:
                    stringout += "\n"

        # print(stringout, end = '', flush = True)
        self.output_buffer += stringout


    def getBuffer(self):
        buffer = self.output_buffer
        self.output_buffer = ""
        return buffer


    def get_frequency(self):
        most_common_frequency = 0

        if len(self.frequency_history) > 0:
            histogram = Counter(self.frequency_history)
            (most_common_frequency, count) = histogram.most_common(1)[0]
            # self.frequency_history = []

        if self.frequency_auto_tune:
            self.FREQ = most_common_frequency

        return most_common_frequency

    def get_wps(self):

        real_wps = 0
        dit_duration = 0
        dash_duration = 0

        if len(self.beep_duration_history) > 0:
            histogram = Counter(self.beep_duration_history)
            beep_durations = histogram.most_common(2)
            if (len(beep_durations)) == 2:
                (dit_duration, count) = beep_durations[0]
                (dash_duration, count) = beep_durations[1]

                if dit_duration > dash_duration:
                    tmp_duration = dit_duration
                    dit_duration = dash_duration
                    dash_duration = tmp_duration

        return (dit_duration, dash_duration)