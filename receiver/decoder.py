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

    sound_level_threshold = 1200
    sound_level_autotune = True
    SNR = 0.7
    THRESHOLD_LOW_LIMIT = 50

    smooth_window_len = 6
    smooth_window_type = 'blackman'
    smooth_cut_off_offset = 0.0

    wpm = 20
    wpm_variance = 35  # percent
    wpm_autotune = True

    frequency = 650
    frequency_auto_tune = True
    frequency_variance = 10  # percent

    FREQUENCY_LOW_LIMIT = 300
    FREQUENCY_HIGH_LIMIT = 1000
    frequency_min = int(frequency * ((100 - frequency_variance) / 100))
    frequency_max = int(frequency * ((100 + frequency_variance) / 100))

    RATE = 44100  # frames per a second
    CHUNK_LENGTH_MS = 10

    chunk = int(RATE / 1000 * CHUNK_LENGTH_MS)
    window = numpy.blackman(chunk)

    frequency_history = []
    beep_duration_history = []
    sound_level_history = []
    keep_history_sec = 5
    morse_ascii_history = ""

    keep_number_of_chunks = int(1000 / CHUNK_LENGTH_MS * keep_history_sec)

    LETTER_TO_MORSE = {" ": "/", "A": "·-", "B": "-···", "C": "-·-·", "D": "-··", "E": "·", "F": "··-·", "G": "--·", "H": "····",
                       "I": "··", "J": "·---", "K": "-·-", "L": "·-··", "M": "--", "N": "-·", "O": "---", "P": "·--·",
                       "Q": "--·-", "R": "·-·", "S": "···", "T": "-", "U": "··-", "V": "···-", "W": "·--", "X": "-··-",
                       "Y": "-·--", "Z": "--··", "1": "·----", "2": "··---", "3": "···--", "4": "····-", "5": "·····",
                       "6": "-····", "7": "--···", "8": "---··", "9": "----·", "0": "-----", "?": "··--··",
                       ".": "·-·-·-", ",": "--··--", "!": "-·-·--", "'": "·----·"}

    def __init__(self):

        self.stop_is_requested = False

        self.calculate_timings()

        self.graph_is_saving = False
        self.graph_save_sec = 2
        self.graph_sound_data = []
        self.graph_indata = None
        self.graph_fft_data = None
        self.graph_frequency_data = []
        self.graph_sound_level_data = []
        self.graph_sound_sequence = []
        self.graph_sound_sequence_smoothed = []
        self.graph_sound_sequence_restored = []
        self.graph_sound_level_autotune = []
        self.graph_frequency_autotune_min = []
        self.graph_frequency_autotune_max = []
        self.graph_beep_duration = numpy.zeros(shape=(2, 1))
        self.graph_all_peak_indexes = []
        self.graph_largest_peak_indexes = []
        self.graph_number_of_chunks_collected = 0

        self.output_buffer = ""
        self.last_returned_buffer = ""

    def stop(self):
        self.stop_is_requested = True

    def calculate_timings(self):

        # morse code timing
        self.dah_dot_ratio = 3
        self.dah_dit_ratio_variance = 15  # percent
        self.dit_length_ms = int(1200 / self.wpm)
        self.dah_length_ms = self.dit_length_ms * self.dah_dot_ratio
        self.char_space_length_ms = self.dit_length_ms
        self.letter_space_length_ms = self.dit_length_ms * self.dah_dot_ratio
        self.word_space_length_ms = self.dit_length_ms * 7

        # morse code timing variances in frames
        self.dit_length_min = int(
            self.dit_length_ms * ((100 - self.wpm_variance) / 100) / self.CHUNK_LENGTH_MS)
        self.dit_length_max = int(
            self.dit_length_ms * ((100 + self.wpm_variance) / 100) / self.CHUNK_LENGTH_MS)
        self.dah_length_min = self.dit_length_min * 3
        self.dah_length_max = self.dit_length_max * 3
        self.char_space_length_min = self.dit_length_min
        self.char_space_length_max = self.dit_length_max
        self.letter_space_length_min = self.dit_length_min * 3
        self.letter_space_length_max = self.dit_length_max * 3
        self.word_space_length_min = self.dit_length_min * 7
        self.word_space_length_max = self.dit_length_max * 7

        self.cutoff_threshold = self.letter_space_length_min  # process letter by letter

    def is_silent(self, sound_level):
        "Returns 'True' if below the 'silent' threshold"
        if sound_level > self.THRESHOLD_LOW_LIMIT:
            self.sound_level_history.append(int(sound_level))
            self.sound_level_history = self.sound_level_history[-self.keep_number_of_chunks:]
        return sound_level < self.sound_level_threshold

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

    def smooth_array(self, array, window_len=5, window_type='hanning'):

        if array.ndim != 1:
            raise ValueError("smooth only accepts 1 dimension arrays.")

        if array.size < window_len:
            return array

        if window_len < 3:
            return array

        if not window_type in ['flat', 'hanning', 'hamming', 'bartlett', 'blackman']:
            raise ValueError(
                "Window is on of 'flat', 'hanning', 'hamming', 'bartlett', 'blackman'")

        s = numpy.r_[array[window_len-1:0:-1],
                     array, array[-2:-window_len-1:-1]]

        if window_type == 'flat':  # moving average
            window_array = numpy.ones(window_len, 'd')
        else:
            window_array = eval('numpy.'+window_type+'(window_len)')

        smoothed_array = numpy.convolve(
            window_array/window_array.sum(), s, mode='valid')

        # adjust the array length
        smoothed_array = smoothed_array[int(window_len/2-1):-int(window_len/2)]

        return smoothed_array

    def decode(self, morse_decoder_queue):
        self.stop_is_requested = False
        sound_started = False
        syncronized = False
        num_silent = 0
        sound_sequence = []

        while not self.stop_is_requested:
            sound_data = morse_decoder_queue.get()

            if self.graph_is_saving:
                if self.graph_number_of_chunks_collected >= int(self.graph_save_sec / self.CHUNK_LENGTH_MS * 1000):
                    self.graph_is_saving = False
                    self.save_plot()
                else:
                    self.graph_sound_data += sound_data
                    self.graph_number_of_chunks_collected += 1

            if sound_data is None:
                continue

            if byteorder == 'big':
                sound_data.byteswap()

            # snd_data = self.normalize(snd_data)

            # r.extend(snd_data)
            # sample_width = p.get_sample_size(self.FORMAT)

            # find frequency of each chunk
            indata = numpy.array(wave.struct.unpack(
                "%dh" % (self.chunk), sound_data)) * self.window
            if self.graph_is_saving:
                self.graph_indata = numpy.append(self.graph_indata, indata)

            # take fft and square each value
            fft_data_square = abs(numpy.fft.rfft(indata)) ** 2
            if self.graph_is_saving:
                self.graph_fft_data = numpy.append(
                    self.graph_fft_data, fft_data_square)

            # find the maximum
            which = fft_data_square[1:].argmax() + 1

            sound_level = max(indata)
            if self.graph_is_saving:
                self.graph_sound_level_data.append(sound_level)
                self.get_sound_level()
                self.graph_sound_level_autotune.append(self.sound_level_threshold)

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

            if self.graph_is_saving:
                self.graph_frequency_data.append(frequency)
                self.get_frequency()
                self.graph_frequency_autotune_min.append(self.frequency_min)
                self.graph_frequency_autotune_max.append(self.frequency_max)

            # keep last 5 sec of frequency measurements
            if frequency >= self.FREQUENCY_LOW_LIMIT and frequency <= self.FREQUENCY_HIGH_LIMIT:
                self.frequency_history.append(round(frequency, 0))
                self.frequency_history = self.frequency_history[-self.keep_number_of_chunks:]

            if frequency >= self.frequency_min and frequency <= self.frequency_max:
                self.graph_sound_sequence.append(1)
                # check if this is a new character started
                if num_silent >= self.letter_space_length_min and sound_started and syncronized:
                    self.decode_morse_sequence(sound_sequence)
                    num_silent = 0
                    sound_sequence = []
                if syncronized:
                    sound_sequence.append(1)
                num_silent = 0
                sound_started = True
            elif sound_started:
                self.graph_sound_sequence.append(0)
                num_silent += 1
                if syncronized:
                    sound_sequence.append(0)
            else:
                # waiting for long selence so don't break a word
                self.graph_sound_sequence.append(0)
                num_silent += 1

            if num_silent >= self.word_space_length_min and sound_started:
                if sound_started and syncronized:
                    self.decode_morse_sequence(sound_sequence)
                num_silent = 0
                sound_sequence = []
                sound_started = False
                syncronized = True

        return            

    def generate_plot(self):

        self.graph_sound_data = []
        self.graph_indata = numpy.empty((0, 3), float)
        self.graph_fft_data = numpy.empty((0, 3), float)
        self.graph_frequency_data = []
        self.graph_sound_level_data = []
        self.graph_sound_sequence = []
        self.graph_sound_sequence_smoothed = []
        self.graph_sound_sequence_restored = []
        self.graph_sound_level_autotune = []
        self.graph_frequency_autotune_min = []
        self.graph_frequency_autotune_max = []
        self.graph_number_of_chunks_collected = 0
        self.graph_is_saving = True

    def save_plot(self):

        import matplotlib.pyplot as plt

        plt.switch_backend('Agg')  # don't try to create a GUI window

        snr = self.signaltonoise(self.graph_indata, 0, 0)

        fig, axs = plt.subplots(8)
        fig.set_size_inches(32, 18)
        # fig.suptitle('graph PLOT')
        axs[0].set_title("Unpacked input bytes (SNR={:3.4f})".format(snr))
        axs[1].set_title("Square of FFT data")
        axs[2].set_title("Sound level")
        axs[3].set_title("Detected frequency")
        axs[4].set_title("Sound sequence")
        axs[5].set_title("Sound sequence smoothed")
        axs[6].set_title("Sound sequence restored")
        axs[7].set_title("Beep Durations")
        #axs[3].set_ylim(ymin=0, auto=True)
        #axs[0].grid(color='r', linestyle='-', linewidth=0.5)

        lines_color = 'r'
        line_width = 0.5
        axs[0].plot(numpy.linspace(0, self.graph_save_sec, len(self.graph_indata)), self.graph_indata,
                    linewidth=line_width, color=lines_color)
        axs[1].plot(numpy.linspace(0, self.graph_save_sec, len(self.graph_fft_data)), self.graph_fft_data, linewidth=line_width,
                    color=lines_color)
        axs[2].plot(numpy.linspace(0, self.graph_save_sec, len(self.graph_sound_level_data)), self.graph_sound_level_data,
                    linewidth=line_width, color=lines_color)
        axs[3].plot(numpy.linspace(0, self.graph_save_sec, len(self.graph_frequency_data)), self.graph_frequency_data,
                    linewidth=line_width, color=lines_color)
        axs[4].plot(numpy.linspace(0, self.graph_save_sec, len(self.graph_sound_sequence)),
                    self.graph_sound_sequence, linewidth=line_width * 2, color=lines_color)
        self.graph_sound_sequence_smoothed = self.smooth_array(numpy.array(
            self.graph_sound_sequence, dtype=numpy.float64), window_len=self.smooth_window_len, window_type=self.smooth_window_type)
        axs[5].plot(numpy.linspace(0, self.graph_save_sec, len(self.graph_sound_sequence_smoothed)), self.graph_sound_sequence_smoothed,
                    linewidth=line_width, color=lines_color)
        self.graph_sound_sequence_restored = numpy.around(
            self.graph_sound_sequence_smoothed - self.smooth_cut_off_offset).astype(int)
        axs[6].plot(numpy.linspace(0, self.graph_save_sec, len(self.graph_sound_sequence_restored)),
                    self.graph_sound_sequence_restored, linewidth=line_width * 2, color=lines_color)
        axs[7].plot(self.graph_beep_duration[0], self.graph_beep_duration[1],
                    linewidth=line_width * 2, color=lines_color)
        axs[7].plot(self.graph_beep_duration[0][self.graph_all_peak_indexes],
                    self.graph_beep_duration[1][self.graph_all_peak_indexes], 'o')
        axs[7].plot(self.graph_beep_duration[0][self.graph_largest_peak_indexes],
                    self.graph_beep_duration[1][self.graph_largest_peak_indexes], 'o')

        horizontal_lines_width = 0.5
        horizontal_lines_color = 'b'

        axs[2].plot(numpy.linspace(0, self.graph_save_sec, len(self.graph_sound_level_autotune)),
                    self.graph_sound_level_autotune,
                    linewidth=horizontal_lines_width, color=horizontal_lines_color)
        axs[3].plot(numpy.linspace(0, self.graph_save_sec, len(self.graph_frequency_autotune_min)),
                    self.graph_frequency_autotune_min, linewidth=horizontal_lines_width,
                    color=horizontal_lines_color)
        axs[3].plot(numpy.linspace(0, self.graph_save_sec, len(self.graph_frequency_autotune_max)),
                    self.graph_frequency_autotune_max, linewidth=horizontal_lines_width,
                    color=horizontal_lines_color)                    
        axs[5].axhline(0.5 + self.smooth_cut_off_offset, linewidth=horizontal_lines_width,
                       color=horizontal_lines_color, linestyle='dotted')

        if self.graph_save_sec <= 1:
            vertical_lines_width = 0.2
            vertical_lines_color = 'k'
            vertical_marks = numpy.arange(
                0, self.graph_save_sec + self.CHUNK_LENGTH_MS / 1000, self.CHUNK_LENGTH_MS / 1000)
            for plot_index in range(0, 6+1):
                for x in vertical_marks:
                    axs[plot_index].axvline(x, linewidth=vertical_lines_width,
                                            color=vertical_lines_color)

        fig.subplots_adjust(left=0.03, right=0.98,
                            top=0.95, bottom=0.05, wspace=0.2, hspace=0.4)

        fig.savefig("debug_plot.png")
        # numpy.savetxt('data.csv', numpy.array(
        #     self.beep_duration_history, dtype=numpy.int16), fmt='%d', delimiter=',')

    def decode_morse_sequence(self, morse_sequence):
        # print(list)

        line_breakers = ".?!"
        last_character = ""

        morse_sequence = numpy.array(morse_sequence)

        # smooth array
        morse_sequence_smoothed = self.smooth_array(numpy.array(
            morse_sequence, dtype=numpy.float64), window_len=self.smooth_window_len, window_type=self.smooth_window_type)

        # restore array
        morse_sequence_restored = numpy.around(
            morse_sequence_smoothed - self.smooth_cut_off_offset).astype(int)
        # correct the array after restore
        morse_sequence_restored = numpy.delete(morse_sequence_restored, 0)
        morse_sequence_restored = numpy.append(morse_sequence_restored, 0)


        counter = 0
        sounding = False
        morse_ascii = ""
        for i in range(len(morse_sequence_restored)):
            if morse_sequence_restored[i] == 1:
                if sounding:
                    counter += 1
                else:  # a silence ended
                    if counter >= self.char_space_length_min and counter <= self.char_space_length_max:
                        None  # listascii += ""
                    elif counter >= self.letter_space_length_min and counter <= self.letter_space_length_max:
                        morse_ascii += " "

                    counter = 1
                    sounding = True
            else:
                if not sounding:
                    counter += 1
                    if counter >= self.word_space_length_min:
                        morse_ascii += " /"
                        counter = 1
                else:  # a beep ended, let's decide is it dit or dah
                    if counter >= self.dit_length_min and counter <= self.dit_length_max:
                        morse_ascii += "·"
                    elif counter >= self.dah_length_min and counter <= self.dah_length_max:
                        morse_ascii += "-"

                    self.beep_duration_history.append(counter)
                    self.beep_duration_history = self.beep_duration_history[-50:]
                    counter = 1
                    sounding = False

        self.morse_ascii_history += morse_ascii + " "
        self.morse_ascii_history = self.morse_ascii_history[-250:]
        morse_ascii = morse_ascii.split(" ")
        stringout = ""
        for i in range(len(morse_ascii)):
            if morse_ascii[i] == "":
                if not last_character in line_breakers:
                    stringout += " "  # drop space in the beginning of a line
            else:
                letter_found = False
                for letter, morse in self.LETTER_TO_MORSE.items():
                    if morse_ascii[i] == morse:
                        stringout += letter
                        last_character = letter
                        letter_found = True
                if not letter_found:
                    last_character = "_"
                    stringout += last_character
                if last_character in line_breakers:
                    None  # stringout += "\n"

        # print(stringout, end = '', flush = True)
        self.output_buffer += stringout

    def getBuffer(self):

        buffer = ""

        if self.output_buffer.strip() or self.last_returned_buffer.strip():
            buffer = self.output_buffer
            self.last_returned_buffer = self.output_buffer
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

        if self.frequency_auto_tune:
            return most_common_frequency
        else:
            return self.frequency

    def get_wpm(self):

        wpm_reliable = False

        if not self.wpm_autotune:
            self.calculate_timings()
            return ">{:2d}<".format(self.wpm)

        if len(self.beep_duration_history) < 50:
            return "?{:2d}?".format(self.wpm)

        histogram = Counter(self.beep_duration_history)

        # sort and transpose the histogram
        beep_durations = sorted(histogram.items())
        beep_durations = numpy.array(beep_durations)
        beep_durations = beep_durations.transpose()

        if self.graph_is_saving:
            self.graph_beep_duration = beep_durations

        durations = beep_durations[0]
        counters = beep_durations[1]

        tolerance = 0.75
        diffs = numpy.diff(counters)
        extrema = numpy.where(diffs > tolerance)[0] + 1
        peak_indexes = numpy.append(extrema, 0)
        peak_counters = counters[peak_indexes]

        if self.graph_is_saving:
            self.graph_all_peak_indexes = peak_indexes

        # all_peak_indexes = numpy.where(
        #     (y[1:-1] > y[0:-2]) * (y[1:-1] > y[2:]))[0] + 1

        if (len(peak_indexes)) < 2:
            return "~{:2d}~".format(self.wpm)

        # get largest peak
        largest_peak_duration = 0 
        largest_peak_index = peak_indexes[numpy.where(
            peak_counters == numpy.amax(peak_counters))[0]][0]
        largest_peak_duration = durations[largest_peak_index]
        while largest_peak_duration < 3 and numpy.amax(peak_counters) > 0:  # remove too short beeps
            # remove largest counter
            peak_counters[numpy.where(
                peak_counters == numpy.amax(peak_counters))[0][0]] = 0
            largest_peak_index = peak_indexes[numpy.where(
                peak_counters == numpy.amax(peak_counters))[0]][0]
            largest_peak_duration = durations[largest_peak_index]

        # try to find second peek so dah/dit ration ~= 3
        # remove largest counter
        peak_counters[numpy.where(
            peak_counters == numpy.amax(peak_counters))[0][0]] = 0
        second_peak_duration = 0     
        while numpy.amax(peak_counters) > 0:    
            second_peak_index = peak_indexes[numpy.where(
                peak_counters == numpy.amax(peak_counters))[0]][0]
            second_peak_duration = durations[second_peak_index]    
            if largest_peak_duration < second_peak_duration:
                dit_duration = largest_peak_duration
                dah_duration = second_peak_duration
            else:
                dit_duration = second_peak_duration
                dah_duration = largest_peak_duration

            if dit_duration > 2: # remove too short beeps
                dah_dit_ratio_detected = dah_duration / dit_duration
            else:
                dah_dit_ratio_detected = 0

            # check beep length calculation reliability          
            if dah_dit_ratio_detected >= self.dah_dot_ratio * (100 - self.dah_dit_ratio_variance) / 100 \
                    and dah_dit_ratio_detected <= self.dah_dot_ratio * (100 + self.dah_dit_ratio_variance) / 100:
                wpm_reliable = True    
                break
            else: 
                peak_counters[numpy.where(
                    peak_counters == numpy.amax(peak_counters))[0][0]] = 0

        # calculate and update WPM
        if wpm_reliable:
            largest_peak_indexes = numpy.array(
                [largest_peak_index, second_peak_index])

            if self.graph_is_saving:
                self.graph_largest_peak_indexes = largest_peak_indexes  

            dit_length_ms = dit_duration * self.CHUNK_LENGTH_MS
            dah_length_ms = dah_duration * self.CHUNK_LENGTH_MS

            wpm = int(round(1200 / dit_length_ms, 0))
            # more accurate ?
            wpm = int(round(1200 / dah_length_ms * 3, 0))

            if self.wpm_autotune and wpm >= 2 and wpm <= 35:
                self.wpm = wpm
                self.calculate_timings()

            return "[{:2d}]".format(self.wpm)
        else:
            return "?{:2d}?".format(self.wpm)

    def get_sound_level(self):
        sound_level = 0

        if len(self.sound_level_history) > 0:

            sound_level = int(numpy.mean(self.sound_level_history))

            if self.sound_level_autotune and sound_level >= self.THRESHOLD_LOW_LIMIT:
                self.sound_level_threshold = int(sound_level * self.SNR)

        return sound_level

    def get_morse_ascii_history(self):    
        return self.morse_ascii_history

    def clear_morse_ascii_history(self):
        self.morse_ascii_history = ""


if __name__ == "__main__":
    decoder = MorseDecoder()
    decoder.graph_is_saving = True
    morse_decoder_queue = Queue(maxsize=1)
    decoder.decode(morse_decoder_queue)
    buffer = decoder.getBuffer()
    print(buffer)
