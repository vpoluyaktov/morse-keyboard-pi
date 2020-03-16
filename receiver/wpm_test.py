import numpy
from collections import Counter
import matplotlib.pyplot as plt


class WPMTest:

    RATE = 44100  # frames per a second
    CHUNK_LENGTH_MS = 10
    chunk = int(RATE / 1000 * CHUNK_LENGTH_MS)

    wpm = 20
    wpm_variance = 25  # percent

    def calculate_timings(self):

        # morse code timing
        self.dit_length_ms = int(1200 / self.wpm)
        self.dah_length_ms = self.dit_length_ms * 3
        self.char_space_length_ms = self.dit_length_ms
        self.letter_space_length_ms = self.dit_length_ms * 3
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

    def get_wpm(self):

        beep_duration_history = numpy.loadtxt('data.csv', dtype=int)

        histogram = Counter(beep_duration_history)

        # sort and transpose the histogram
        beep_durations = sorted(histogram.items())
        beep_durations = numpy.array(beep_durations)
        beep_durations = beep_durations.transpose()

        x = beep_durations[0]
        y = beep_durations[1]

        x = [4,  5, 12, 13]
        y = [20, 11, 11,  8]

        all_peak_indexes = numpy.where(
            (y[1:-1] > y[0:-2]) * (y[1:-1] > y[2:]))[0] + 1

        if (len(all_peak_indexes)) < 2:
            return self.wpm    

        # get two largest peaks
        peak_values = y[all_peak_indexes]
        largest_peak_index = all_peak_indexes[numpy.where(
            peak_values == numpy.amax(peak_values))[0]][0]
        peak_values[numpy.where(peak_values == numpy.amax(peak_values))[0][0]] = 0
        second_peak_index = all_peak_indexes[numpy.where(
            peak_values == numpy.amax(peak_values))[0]][0]
        largest_peak_indexes = numpy.array(
            [largest_peak_index, second_peak_index])

        if x[largest_peak_index] < x[second_peak_index]:
            dit_duration = x[largest_peak_index]
            dah_duration = x[second_peak_index]
        else:
            dit_duration = x[second_peak_index]
            dah_duration = x[largest_peak_index]

        if dit_duration > 0:
            dah_dot_ratio = dah_duration / dit_duration
        else:
            dah_dot_ratio = 0

        dah_dot_ratio_ideal = 3
        dah_dot_ratio_variance = 10  # persent

        # check beep length calculation reliability
        wpm_reliable = False
        if dah_dot_ratio >= dah_dot_ratio_ideal * (100 - dah_dot_ratio_variance) / 100 \
                and dah_dot_ratio <= dah_dot_ratio_ideal * (100 + dah_dot_ratio_variance) / 100:
            wpm_reliable = True

        # calculate and update WPM
        if wpm_reliable:
            dit_length_ms = dit_duration * self.CHUNK_LENGTH_MS
            dah_length_ms = dah_duration * self.CHUNK_LENGTH_MS

            self.wpm = int(round(1200 / dit_length_ms, 0))
            # more accurate ?
            self.wpm = int(round(1200 / dah_length_ms * 3, 0))
            self.calculate_timings()

       

        fig, axs = plt.subplots(3)

        axs[0].set_title("Beep Durations")

        axs[0].plot(x, y)
        axs[0].plot(x[all_peak_indexes], y[all_peak_indexes], 'o')
        axs[0].plot(x[largest_peak_indexes], y[largest_peak_indexes], 'X')

        plt.ion()
        fig.show()

        return (self.wpm)


if __name__ == '__main__':

    test = WPMTest()
    test.calculate_timings()
    test.get_wpm()
    input("Press [enter] to continue.")
    print("done")
