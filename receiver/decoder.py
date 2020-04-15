from sys import byteorder
from array import array
from struct import pack
from collections import Counter
import os
import warnings
import wave
from time import sleep
from queue import Queue
import numpy as np

from utils.config import Config

warnings.filterwarnings("ignore", message="divide by zero encountered")
warnings.filterwarnings("ignore", message="invalid value encountered")
warnings.filterwarnings("ignore", message="Evaluate error")
warnings.filterwarnings("ignore", message="Unknown PCM")
warnings.filterwarnings("ignore", message="ALSA")

class MorseDecoder:

    config = Config()

    frequency_min = int(config.receiver_frequency  * ((100 - config.frequency_variance) / 100))
    frequency_max = int(config.receiver_frequency  * ((100 + config.frequency_variance) / 100))

    chunk = int(config.RATE  / 1000 * config.CHUNK_LENGTH_MS)
    window = np.blackman(chunk)

    frequency_history = []
    beep_duration_history = []
    beep_duration_history_lenght = 10
    sound_level_history = []
    keep_history_sec = 3
    morse_ascii_history = ""

    keep_number_of_chunks = int(1000 / config.CHUNK_LENGTH_MS * keep_history_sec)

    LETTER_TO_MORSE = {" ": "/", "A": "·−", "B": "−···", "C": "−·−·", "D": "−··", "E": "·", "F": "··−·", "G": "−−·", "H": "····",
                       "I": "··", "J": "·−−−", "K": "−·−", "L": "·−··", "M": "−−", "N": "−·", "O": "−−−", "P": "·−−·",
                       "Q": "−−·−", "R": "·−·", "S": "···", "T": "−", "U": "··−", "V": "···−", "W": "·−−", "X": "−··−",
                       "Y": "−·−−", "Z": "−−··", "1": "·−−−−", "2": "··−−−", "3": "···−−", "4": "····−", "5": "·····",
                       "6": "−····", "7": "−−···", "8": "−−−··", "9": "−−−−·", "0": "−−−−−", "?": "··−−··",
                       ".": "·−·−·−", ",": "−−··−−", "!": "−·−·−−", "'": "·−−−−·", "/": "−··−·", "&": "·−···",
                       ":": "−−−···", ";": "−·−·−·", "+": "·−·−·", "-": "−····−", "\"": "·−··−·", "$": "···−··−",
                       "@": "·−−·−·", "<AA>": "·−·−", "<BT>": "−···−"}

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
        self.graph_sound_level_threshold = []
        self.graph_frequency_autotune_min = []
        self.graph_frequency_autotune_max = []
        self.graph_beep_duration = np.zeros(shape=(2, 1))
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
        self.dit_duration_ms = int(1200 / self.config.receiver_wpm)
        self.dah_duratino_ms = self.dit_duration_ms * self.dah_dot_ratio
        self.char_space_duration_ms = self.dit_duration_ms
        self.letter_space_durarion_ms = self.dit_duration_ms * self.dah_dot_ratio
        self.word_space_length_ms = self.dit_duration_ms * 7

        # morse code timing variances in frames
        self.dit_length_chunks_min = int(
            self.dit_duration_ms * ((100 - self.config.wpm_variance) / 100) / self.config.CHUNK_LENGTH_MS)
        self.dit_length_chunks_max = int(
            self.dit_duration_ms * ((100 + self.config.wpm_variance) / 100) / self.config.CHUNK_LENGTH_MS)
        self.dah_length_chunks_min = self.dit_length_chunks_min * 3
        self.dah_length_chunks_max = self.dit_length_chunks_max * 3
        self.char_space_length_chunks_min = self.dit_length_chunks_min
        self.char_space_length_chunks_max = self.dit_length_chunks_max
        self.letter_space_length_chunks_min = self.dit_length_chunks_min * 3
        self.letter_space_length_chunks_max = self.dit_length_chunks_max * 3
        self.word_space_length_chunks_min = self.dit_length_chunks_min * 7
        self.word_space_length_chunks_max = self.dit_length_chunks_max * 7

        self.cutoff_threshold = self.letter_space_length_chunks_min  # process letter by letter

    def is_silent(self, sound_level):
        "Returns 'True' if below the 'silent' threshold"
        # if sound_level >= self.config.THRESHOLD_LOW_LIMIT:
        self.sound_level_history.append(int(sound_level))
        self.sound_level_history = self.sound_level_history[-self.keep_number_of_chunks:]
        return sound_level < self.config.sound_level_threshold

    def signaltonoise(self, data, axis=0, ddof=0):
        data = np.asanyarray(data)
        m = data.mean(axis)
        sd = data.std(axis=axis, ddof=ddof)
        snr_array = np.where(sd == 0, 0, m / sd)
        snr = snr_array.tolist()
        # snr = np.log10(snr)
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

        s = np.r_[array[window_len-1:0:-1],
                     array, array[-2:-window_len-1:-1]]

        if window_type == 'flat':  # moving average
            window_array = np.ones(window_len, 'd')
        else:
            window_array = eval('np.'+window_type+'(window_len)')

        smoothed_array = np.convolve(
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
                if self.graph_number_of_chunks_collected >= int(self.graph_save_sec / self.config.CHUNK_LENGTH_MS * 1000):
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
            indata = np.array(wave.struct.unpack(
                "%dh" % (self.chunk), sound_data)) * self.window
            if self.graph_is_saving:
                self.graph_indata = np.append(self.graph_indata, indata)

            # take fft and square each value
            fft_data_square = abs(np.fft.rfft(indata)) ** 2
            if self.graph_is_saving:
                self.graph_fft_data = np.append(
                    self.graph_fft_data, fft_data_square)

            # find the maximum
            which = fft_data_square[1:].argmax() + 1

            sound_level = max(indata)
            if self.graph_is_saving:
                self.graph_sound_level_data.append(sound_level)
                self.get_sound_level()
                self.graph_sound_level_threshold.append(
                    self.config.sound_level_threshold)

            silent = self.is_silent(sound_level)

            if silent:
                frequency = 0
            elif which != len(fft_data_square) - 1:
                try:
                    y0, y1, y2 = np.log(
                        fft_data_square[which - 1:which + 2:])
                    x1 = (y2 - y0) * .5 / (2 * y1 - y2 - y0)
                    # find the frequency and output it
                    frequency = (which + x1) * self.config.RATE / self.chunk
                except RuntimeWarning:
                    None
            else:
                frequency = which * self.config.RATE / self.chunk

            if self.graph_is_saving:
                self.graph_frequency_data.append(frequency)
                self.get_frequency()
                self.graph_frequency_autotune_min.append(self.frequency_min)
                self.graph_frequency_autotune_max.append(self.frequency_max)

            # keep last n sec of frequency measurements
            if frequency >= self.config.FREQUENCY_LOW_LIMIT and frequency <= self.config.FREQUENCY_HIGH_LIMIT:
                self.frequency_history.append(round(frequency, 0))
                self.frequency_history = self.frequency_history[-self.keep_number_of_chunks:]

            if frequency >= self.frequency_min and frequency <= self.frequency_max:
                self.graph_sound_sequence.append(1)
                # check if this is a new character started
                if num_silent >= self.letter_space_length_chunks_min and sound_started and syncronized:
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

            if num_silent >= self.word_space_length_chunks_min and sound_started:
                if sound_started and syncronized:
                    self.decode_morse_sequence(sound_sequence)
                num_silent = 0
                sound_sequence = []
                sound_started = False
                syncronized = True

        return

    def generate_plot(self):

        self.graph_sound_data = []
        self.graph_indata = np.empty((0, 3), float)
        self.graph_fft_data = np.empty((0, 3), float)
        self.graph_frequency_data = []
        self.graph_sound_level_data = []
        self.graph_sound_sequence = []
        self.graph_sound_sequence_smoothed = []
        self.graph_sound_sequence_restored = []
        self.graph_sound_level_threshold = []
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
        axs[0].plot(np.linspace(0, self.graph_save_sec, len(self.graph_indata)), self.graph_indata,
                    linewidth=line_width, color=lines_color)
        axs[1].plot(np.linspace(0, self.graph_save_sec, len(self.graph_fft_data)), self.graph_fft_data, linewidth=line_width,
                    color=lines_color)
        axs[2].plot(np.linspace(0, self.graph_save_sec, len(self.graph_sound_level_data)), self.graph_sound_level_data,
                    linewidth=line_width, color=lines_color)
        axs[3].plot(np.linspace(0, self.graph_save_sec, len(self.graph_frequency_data)), self.graph_frequency_data,
                    linewidth=line_width, color=lines_color)
        axs[4].plot(np.linspace(0, self.graph_save_sec, len(self.graph_sound_sequence)),
                    self.graph_sound_sequence, linewidth=line_width * 2, color=lines_color)
        self.graph_sound_sequence_smoothed = self.smooth_array(np.array(
            self.graph_sound_sequence, dtype=np.float64), window_len=self.config.smooth_window_len, window_type=self.config.smooth_window_type)
        axs[5].plot(np.linspace(0, self.graph_save_sec, len(self.graph_sound_sequence_smoothed)), self.graph_sound_sequence_smoothed,
                    linewidth=line_width, color=lines_color)
        self.graph_sound_sequence_restored = np.around(
            self.graph_sound_sequence_smoothed - self.config.smooth_cut_off_offset).astype(int)
        axs[6].plot(np.linspace(0, self.graph_save_sec, len(self.graph_sound_sequence_restored)),
                    self.graph_sound_sequence_restored, linewidth=line_width * 2, color=lines_color)
        axs[7].plot(self.graph_beep_duration[0], self.graph_beep_duration[1],
                    linewidth=line_width * 2, color=lines_color)
        axs[7].plot(self.graph_beep_duration[0][self.graph_all_peak_indexes],
                    self.graph_beep_duration[1][self.graph_all_peak_indexes], 'o')
        axs[7].plot(self.graph_beep_duration[0][self.graph_largest_peak_indexes],
                    self.graph_beep_duration[1][self.graph_largest_peak_indexes], 'o')

        horizontal_lines_width = 0.5
        horizontal_lines_color = 'b'

        axs[2].plot(np.linspace(0, self.graph_save_sec, len(self.graph_sound_level_threshold)),
                    self.graph_sound_level_threshold,
                    linewidth=horizontal_lines_width, color=horizontal_lines_color)
        axs[3].plot(np.linspace(0, self.graph_save_sec, len(self.graph_frequency_autotune_min)),
                    self.graph_frequency_autotune_min, linewidth=horizontal_lines_width,
                    color=horizontal_lines_color)
        axs[3].plot(np.linspace(0, self.graph_save_sec, len(self.graph_frequency_autotune_max)),
                    self.graph_frequency_autotune_max, linewidth=horizontal_lines_width,
                    color=horizontal_lines_color)
        axs[5].axhline(0.5 + self.config.smooth_cut_off_offset, linewidth=horizontal_lines_width,
                       color=horizontal_lines_color, linestyle='dotted')

        if self.graph_save_sec <= 1:
            vertical_lines_width = 0.2
            vertical_lines_color = 'k'
            vertical_marks = np.arange(
                0, self.graph_save_sec + self.config.CHUNK_LENGTH_MS / 1000, self.config.CHUNK_LENGTH_MS / 1000)
            for plot_index in range(0, 6+1):
                for x in vertical_marks:
                    axs[plot_index].axvline(x, linewidth=vertical_lines_width,
                                            color=vertical_lines_color)

        fig.subplots_adjust(left=0.03, right=0.98,
                            top=0.95, bottom=0.05, wspace=0.2, hspace=0.4)

        fig.savefig("debug_plot.png")
        # np.savetxt('data.csv', np.array(
        #     self.beep_duration_history, dtype=np.int16), fmt='%d', delimiter=',')

    def decode_morse_sequence(self, morse_sequence):
        # print(list)

        line_breakers = ".?!"
        last_character = ""

        morse_sequence = np.array(morse_sequence)

        # smooth array
        morse_sequence_smoothed = self.smooth_array(np.array(
            morse_sequence, dtype=np.float64), window_len=self.config.smooth_window_len, window_type=self.config.smooth_window_type)

        # restore array
        morse_sequence_restored = np.around(
            morse_sequence_smoothed - self.config.smooth_cut_off_offset).astype(int)
        # correct the array after restore
        morse_sequence_restored = np.delete(morse_sequence_restored, 0)
        morse_sequence_restored = np.append(morse_sequence_restored, 0)

        counter = 0
        sounding = False
        morse_ascii = ""
        for i in range(len(morse_sequence_restored)):
            if morse_sequence_restored[i] == 1:
                if sounding:
                    counter += 1
                else:  # a silence ended
                    if counter >= self.char_space_length_chunks_min and counter <= self.char_space_length_chunks_max:
                        None  # listascii += ""
                    elif counter >= self.letter_space_length_chunks_min and counter <= self.letter_space_length_chunks_max:
                        morse_ascii += " "

                    counter = 1
                    sounding = True
            else:
                if not sounding:
                    counter += 1
                    if counter >= self.word_space_length_chunks_min:
                        morse_ascii += " /"
                        counter = 1
                else:  # a beep ended, let's decide is it dit or dah
                    if counter >= self.dit_length_chunks_min and counter <= self.dit_length_chunks_max:
                        morse_ascii += "·"
                    elif counter >= self.dah_length_chunks_min and counter <= self.dah_length_chunks_max:
                        morse_ascii += "−"

                    self.beep_duration_history.append(counter)
                    self.beep_duration_history = self.beep_duration_history[-self.beep_duration_history_lenght:]
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

    def get_buffer(self):

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

        if self.config.frequency_auto_tune and most_common_frequency >= self.config.FREQUENCY_LOW_LIMIT and most_common_frequency <= self.config.FREQUENCY_HIGH_LIMIT:
            if abs(self.config.receiver_frequency - most_common_frequency) > 25:
                self.output_buffer += self.config.MESSAGE_SEPARATOR
            self.config.receiver_frequency = most_common_frequency

        self.frequency_min = int(
            self.config.receiver_frequency * ((100 - self.config.frequency_variance) / 100))
        self.frequency_max = int(
            self.config.receiver_frequency * ((100 + self.config.frequency_variance) / 100))

        if self.config.frequency_auto_tune:
            return most_common_frequency
        else:
            return self.config.receiver_frequency

    def get_wpm(self):

        self.config.wpm_reliable = False

        if not self.config.wpm_autotune:
            self.calculate_timings()
            return ">{:2d}<".format(self.config.receiver_wpm)

        if len(self.beep_duration_history) < self.beep_duration_history_lenght:
            return "?{:2d}?".format(self.config.receiver_wpm)

        histogram = Counter(self.beep_duration_history)

        # sort and transpose the histogram
        beep_durations = sorted(histogram.items())
        beep_durations = np.array(beep_durations)
        beep_durations = beep_durations.transpose()

        if self.graph_is_saving:
            self.graph_beep_duration = beep_durations

        durations = beep_durations[0]
        counters = beep_durations[1]

        tolerance = 0.75
        diffs = np.diff(counters)
        extrema = np.where(diffs > tolerance)[0] + 1
        peak_indexes = np.append(extrema, 0)
        peak_counters = counters[peak_indexes]

        if self.graph_is_saving:
            self.graph_all_peak_indexes = peak_indexes

        # all_peak_indexes = np.where(
        #     (y[1:-1] > y[0:-2]) * (y[1:-1] > y[2:]))[0] + 1

        if (len(peak_indexes)) < 2:
            return "~{:2d}~".format(self.config.receiver_wpm)

        # get largest peak
        largest_peak_duration = 0
        largest_peak_index = peak_indexes[np.where(
            peak_counters == np.amax(peak_counters))[0]][0]
        largest_peak_duration = durations[largest_peak_index]
        # remove too short beeps
        while largest_peak_duration < 3 and np.amax(peak_counters) > 0:
            # remove largest counter
            peak_counters[np.where(
                peak_counters == np.amax(peak_counters))[0][0]] = 0
            largest_peak_index = peak_indexes[np.where(
                peak_counters == np.amax(peak_counters))[0]][0]
            largest_peak_duration = durations[largest_peak_index]

        # try to find second peek so dah/dit ration ~= 3
        # remove largest counter
        peak_counters[np.where(
            peak_counters == np.amax(peak_counters))[0][0]] = 0
        second_peak_duration = 0
        while np.amax(peak_counters) > 0:
            # it looks like there is a bug here with second_peak_index calculation - sometimes it's bigger than the length
            # of the beep_duration array
            # need to investigate
            second_peak_index = peak_indexes[np.where(
                peak_counters == np.amax(peak_counters))[0]][0]
            second_peak_duration = durations[second_peak_index]
            if largest_peak_duration < second_peak_duration:
                dit_duration = largest_peak_duration
                dah_duration = second_peak_duration
            else:
                dit_duration = second_peak_duration
                dah_duration = largest_peak_duration

            if dit_duration > 2:  # remove too short beeps
                dah_dit_ratio_detected = dah_duration / dit_duration
            else:
                dah_dit_ratio_detected = 0

            # check beep length calculation reliability
            if dah_dit_ratio_detected >= self.dah_dot_ratio * (100 - self.dah_dit_ratio_variance) / 100 \
                    and dah_dit_ratio_detected <= self.dah_dot_ratio * (100 + self.dah_dit_ratio_variance) / 100:
                self.config.wpm_reliable = True
                break
            else:
                peak_counters[np.where(
                    peak_counters == np.amax(peak_counters))[0][0]] = 0

        # calculate and update WPM
        if self.config.wpm_reliable:
            largest_peak_indexes = np.array(
                [largest_peak_index, second_peak_index])

            if self.graph_is_saving:
                self.graph_largest_peak_indexes = largest_peak_indexes

            dit_length_ms = dit_duration * self.config.CHUNK_LENGTH_MS
            dah_length_ms = dah_duration * self.config.CHUNK_LENGTH_MS

            self.config.receiver_wpm = int(round(1200 / dit_length_ms, 0))
            # more accurate ?
            self.config.receiver_wpm = int(round(1200 / dah_length_ms * 3, 0))

            if self.config.wpm_autotune and self.config.receiver_wpm >= 2 and self.config.receiver_wpm <= 35:
                self.config.receiver_wpm = self.config.receiver_wpm
                self.calculate_timings()

            return "[{:2d}]".format(self.config.receiver_wpm)
        else:
            return "?{:2d}?".format(self.config.receiver_wpm)

    def get_sound_level(self):
        sound_level = 0

        if len(self.sound_level_history) > 0:

            sound_level = int(np.mean(self.sound_level_history))

            if self.config.sound_level_autotune and sound_level >= self.config.THRESHOLD_LOW_LIMIT:
                self.config.sound_level_threshold = int(sound_level * self.config.SNR)

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
    buffer = decoder.get_buffer()
    print(buffer)
