#!/usr/bin/python3

try:

    from sys import byteorder
    from array import array
    from struct import pack
    from collections import Counter
    import os
    import warnings
    import wave
    from time import sleep
    from queue import Queue

    import numpy

except ImportError as error:
    print("You have to install some extras in order to use this shell script:")
    print(error)
    exit(1)

warnings.filterwarnings("ignore", message="divide by zero encountered")
warnings.filterwarnings("ignore", message="invalid value encountered")
warnings.filterwarnings("ignore", message="Evaluate error")
warnings.filterwarnings("ignore", message="Unknown PCM")
warnings.filterwarnings("ignore", message="ALSA")


class MorseDecoder:
    DEBUG = False
    DEBUG_READ_SEC = 0.2
    debug_input_data = "sound-data.bin"

    output_buffer = ""

    threshold = 1200
    sound_level_autotune = True
    SNR = 0.6
    THRESHOLD_LOW_LIMIT = 50

    wpm = 19
    wpm_variance = 30  # percent

    frequency = 600
    frequency_auto_tune = True
    frequency_variance = 20  # percent

    FREQUENCY_LOW_LIMIT = 400
    FREQUENCY_HIGH_LIMIT = 1000
    frequency_min = int(frequency * ((100 - frequency_variance) / 100))
    frequency_max = int(frequency * ((100 + frequency_variance) / 100))

    RATE = 44100  # frames per a second
    CHUNK_LENGTH_MS = 10
    ALLOWANCE = 3

    chunk = int(RATE / 1000 * CHUNK_LENGTH_MS)
    window = numpy.blackman(chunk)

    frequency_history = []
    beep_duration_history = []
    sound_level_history = []
    keep_history_sec = 5

    keep_number_of_chunks = int(1000 / CHUNK_LENGTH_MS * keep_history_sec)

    # morse code timing
    dit_length_ms = int(1200 / wpm)
    dah_length_ms = dit_length_ms * 3
    char_space_length_ms = dit_length_ms
    letter_space_length_ms = dit_length_ms * 3
    word_space_length_ms = dit_length_ms * 7

    # morse code timing variances in frames
    dit_length_min = int(
        dit_length_ms * ((100 - wpm_variance) / 100) / CHUNK_LENGTH_MS)
    dit_length_max = int(
        dit_length_ms * ((100 + wpm_variance) / 100) / CHUNK_LENGTH_MS)
    dah_length_min = dit_length_min * 3
    dah_length_max = dit_length_max * 3
    char_space_length_min = dit_length_min
    char_space_length_max = dit_length_max
    letter_space_length_min = dit_length_min * 3
    letter_space_length_max = dit_length_max * 3
    word_space_length_min = dit_length_min * 7
    word_space_length_max = dit_length_max * 7

    cutoff_threshold = letter_space_length_min  # process letter by letter

    LETTER_TO_MORSE = {"A": ".-", "B": "-...", "C": "-.-.", "D": "-..", "E": ".", "F": "..-.", "G": "--.", "H": "....",
                       "I": "..", "J": ".---", "K": "-.-", "L": ".-..", "M": "--", "N": "-.", "O": "---", "P": ".--.",
                       "Q": "--.-", "R": ".-.", "S": "...", "T": "-", "U": "..-", "V": "...-", "W": ".--", "X": "-..-",
                       "Y": "-.--", "Z": "--..", "1": ".----", "2": "..---", "3": "...--", "4": "....-", "5": ".....",
                       "6": "-....", "7": "--...", "8": "---..", "9": "----.", "0": "-----", "?": "..--..",
                       ".": ".-.-.-", ",": "--..--", "!": "-.-.--", "'": ".----."}

    def is_silent(self, sound_level):
        "Returns 'True' if below the 'silent' threshold"
        if sound_level > self.THRESHOLD_LOW_LIMIT:
            self.sound_level_history.append(int(sound_level))
            self.sound_level_history = self.sound_level_history[-self.keep_number_of_chunks:]
        return sound_level < self.threshold

    def signaltonoise(self, data, axis=0, ddof=0):
        data = numpy.asanyarray(data)
        m = data.mean(axis)
        sd = data.std(axis=axis, ddof=ddof)
        snr_array = numpy.where(sd == 0, 0, m / sd)
        snr = snr_array.tolist()
        # snr = numpy.log10(snr)
        return snr

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

        debug_sound_data = []
        debug_indata = numpy.empty((0, 3), float)
        debug_fft_data = numpy.empty((0, 3), float)
        debug_frequency_data = []
        debug_sound_level_data = []
        debug_sound_sequence = []
        debug_sound_level_autotune = []
        debug_frequency_autotune_min = []
        debug_frequency_autotune_max = []
        in_file = None
        number_of_chunks_read = 0

        if self.DEBUG:
            in_file = open(self.debug_input_data, "rb")

        while True:
            if self.DEBUG:
                sound_data = in_file.read(self.chunk * 2)
                number_of_chunks_read += 1
                if len(sound_data) < self.chunk * 2 or number_of_chunks_read > int(self.DEBUG_READ_SEC / self.CHUNK_LENGTH_MS * 1000 * 2):
                    break
                debug_sound_data += sound_data
            else:
                sound_data = morse_decoder_queue.get()

            if sound_data is None:
                continue

            if os.environ.get('WRITE_DATA'):
                out_file = open(self.debug_input_data, "ab")
                out_file.write(sound_data)
                out_file.close()

            if byteorder == 'big':
                sound_data.byteswap()

            # snd_data = self.normalize(snd_data)

            # r.extend(snd_data)
            # sample_width = p.get_sample_size(self.FORMAT)

            # find frequency of each chunk
            indata = numpy.array(wave.struct.unpack(
                "%dh" % (self.chunk), sound_data)) * self.window
            if self.DEBUG:
                debug_indata = numpy.append(debug_indata, indata)

            # take fft and square each value
            fft_data_square = abs(numpy.fft.rfft(indata)) ** 2
            if self.DEBUG:
                debug_fft_data = numpy.append(debug_fft_data, fft_data_square)

            # find the maximum
            which = fft_data_square[1:].argmax() + 1

            sound_level = max(indata)
            if self.DEBUG:
                debug_sound_level_data.append(sound_level)
                self.get_sound_level()
                debug_sound_level_autotune.append(self.threshold)

            silent = self.is_silent(sound_level)

            if silent:
                frequency = 0
            elif which != len(fft_data_square) - 1:
                try:
                    y0, y1, y2 = numpy.log(
                        fft_data_square[which - 1:which + 2:])
                    x1 = (y2 - y0) * .5 / (2 * y1 - y2 - y0)
                    # find the frequency and output it
                    frequency = (which + x1) * self.RATE / self.chunk
                except RuntimeWarning:
                    None
            else:
                frequency = which * self.RATE / self.chunk

            if self.DEBUG:
                debug_frequency_data.append(frequency)
                self.get_frequency()
                debug_frequency_autotune_min.append(self.frequency_min)
                debug_frequency_autotune_max.append(self.frequency_max)

            # keep last 5 sec of frequency measurements
            if frequency >= self.FREQUENCY_LOW_LIMIT and frequency <= self.FREQUENCY_HIGH_LIMIT:
                self.frequency_history.append(round(frequency, 0))
                self.frequency_history = self.frequency_history[-self.keep_number_of_chunks:]

            if frequency >= self.frequency_min and frequency <= self.frequency_max:
                debug_sound_sequence += "1"
                # check if this is a new character started
                if num_silent >= self.letter_space_length_min and sound_started and syncronized:
                    self.decode_sequence(sound_sequence)
                    num_silent = 0
                    sound_sequence = ""  # debug_sound_sequence = ""
                if syncronized:
                    sound_sequence += "1"
                num_silent = 0
                sound_started = True
            elif sound_started:
                debug_sound_sequence += "0"
                num_silent += 1
                if syncronized:
                    sound_sequence += "0"
            else:
                # waiting for long selence so don't break a word
                debug_sound_sequence += "0"
                num_silent += 1

            if num_silent >= self.word_space_length_min and sound_started:
                if sound_started and syncronized:
                    self.decode_sequence(sound_sequence)
                num_silent = 0
                sound_sequence = ""
                # debug_sound_sequence = ""
                sound_started = False
                syncronized = True

        if self.DEBUG:
            import matplotlib.pyplot as plt

            snr = self.signaltonoise(debug_indata, 0, 0)

            fig, axs = plt.subplots(5)
            # fig.suptitle('DEBUG PLOT')
            axs[0].set_title("Unpacked input bytes (SNR={:3.4f})".format(snr))
            axs[1].set_title("Square of FFT data")
            axs[2].set_title("Detected frequency")
            axs[3].set_title("Sound level")
            axs[4].set_title("Sound sequence")
            axs[3].set_ylim(ymin=0, auto=True)
            axs[4].set_ylim(ymin=0, ymax=1.5)

            lines_color = 'r'
            line_width = 0.5
            axs[0].plot(debug_indata, linewidth=line_width, color=lines_color)
            axs[1].plot(debug_fft_data, linewidth=line_width,
                        color=lines_color)
            axs[2].plot(debug_frequency_data,
                        linewidth=line_width, color=lines_color)
            axs[3].plot(debug_sound_level_data,
                        linewidth=line_width, color=lines_color)
            axs[4].plot(list(debug_sound_sequence),
                        linewidth=line_width, color=lines_color)

            horizontal_lines_width = 0.2
            horizontal_lines_color = 'b'
            axs[2].plot(debug_frequency_autotune_min, linewidth=horizontal_lines_width,
                        color=horizontal_lines_color)
            axs[2].plot(debug_frequency_autotune_max, linewidth=horizontal_lines_width,
                        color=horizontal_lines_color)
            axs[3].plot(debug_sound_level_autotune,
                        linewidth=horizontal_lines_width, color=horizontal_lines_color)

            if self.DEBUG_READ_SEC <= 2:
                vertical_lines_width = 0.2
                vertical_lines_color = 'k'
                for i in range(len(debug_sound_sequence)):
                    axs[0].axvline(
                        i * self.chunk, linewidth=vertical_lines_width, color=vertical_lines_color)
                    axs[1].axvline(
                        i * self.chunk / 2, linewidth=vertical_lines_width, color=vertical_lines_color)
                    axs[2].axvline(i, linewidth=vertical_lines_width,
                                   color=vertical_lines_color)
                    axs[3].axvline(i, linewidth=vertical_lines_width,
                                   color=vertical_lines_color)
                    axs[4].axvline(i, linewidth=vertical_lines_width,
                                   color=vertical_lines_color)

            fig.subplots_adjust(left=0.03, right=0.98,
                                top=0.95, bottom=0.05, wspace=0.2, hspace=0.4)
            fig.show()

    def decode_sequence(self, list):
        # print(list)

        line_breakers = ".?!"
        last_character = ""

        list = list.split("0")
        listascii = ""
        counter = 0

        # for i in range(len(list)):
        #     if len(list[i]) == 0:  # blank character adds 1
        #         counter += 1
        #     else:
        #         if counter < self.ALLOWANCE:
        #             list[i] += list[i - counter - 1]
        #             list[i - counter - 1] = ""
        #         counter = 0

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
                for letter, morse in self.LETTER_TO_MORSE.items():
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
            (most_common_frequency, count) = histogram.most_common(
                1)[0]  # self.frequency_history = []

        if self.frequency_auto_tune and most_common_frequency >= self.FREQUENCY_LOW_LIMIT and most_common_frequency <= self.FREQUENCY_HIGH_LIMIT:
            self.frequency = most_common_frequency
            self.frequency_min = int(
                self.frequency * ((100 - self.frequency_variance) / 100))
            self.frequency_max = int(
                self.frequency * ((100 + self.frequency_variance) / 100))

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

    def get_sound_level(self):
        beep_level = 0

        if len(self.sound_level_history) > 0:
            # histogram = Counter(self.sound_level_history)
            # sound_levels = histogram.most_common(2)
            #
            # if (len(sound_levels)) == 2:
            #     (beep_level, count) = sound_levels[0]
            #     (silence_level, count) = sound_levels[1]
            #
            #     if beep_level < silence_level:
            #         tmp_duration = beep_level
            #         beep_level = silence_level
            #         silence_level = tmp_duration
            #
            # beep_level = numpy.median(self.sound_level_history)
            beep_level = int(numpy.mean(self.sound_level_history))

            if self.sound_level_autotune and beep_level >= self.THRESHOLD_LOW_LIMIT:
                self.threshold = int(beep_level * self.SNR)

        return beep_level


if __name__ == "__main__":
    decoder = MorseDecoder()
    decoder.DEBUG = True
    morse_decoder_queue = Queue(maxsize=1)
    decoder.decode(morse_decoder_queue)
    buffer = decoder.getBuffer()
    print(buffer)
