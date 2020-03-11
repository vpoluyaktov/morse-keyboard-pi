import numpy
import matplotlib.pyplot as plt


RATE = 44100  # frames per a second
CHUNK_LENGTH_MS = 10
ALLOWANCE = 3

chunk = int(RATE / 1000 * CHUNK_LENGTH_MS)

def smooth_array(array, window_len=11, window='hanning'):

    if array.ndim != 1:
        raise ValueError("smooth only accepts 1 dimension arrays.")

    if array.size < window_len:
        raise ValueError(
            "Input vector needs to be bigger than window size.")

    if window_len < 3:
        return array

    if not window in ['flat', 'hanning', 'hamming', 'bartlett', 'blackman']:
        raise ValueError(
            "Window is on of 'flat', 'hanning', 'hamming', 'bartlett', 'blackman'")

    s = numpy.r_[array[window_len-1:0:-1], array, array[-2:-window_len-1:-1]]

    if window == 'flat':  # moving average
        window_array = numpy.ones(window_len, 'd')
    else:
        window_array = eval('numpy.'+window+'(window_len)')

    smoothed_array = numpy.convolve(
        window_array/window_array.sum(), s, mode='valid')

    # adjust the array length
    smoothed_array = smoothed_array[int(window_len/2-1):-int(window_len/2)]

    return smoothed_array


def smooth_test():

    window_len = 10
    window_type = "blackman"

    input_array = numpy.loadtxt('data.csv')
    smoothed_array = smooth_array(
        input_array, window_len=window_len, window=window_type)
    restored_array = numpy.around(smoothed_array).astype(int)

    fig, axs = plt.subplots(3)
    axs[0].set_title("Input sequence")
    axs[0].plot(input_array)

    axs[1].set_title("Smothed array (window={:d}, type='{:s}')".format(
        window_len, window_type))
    axs[1].plot(smoothed_array)
    axs[1].axhline(0.5, color='r', linestyle='dotted')

    axs[2].set_title("Restored array")
    axs[2].bar(x=numpy.arange(len(restored_array)), height=restored_array, align='edge', width=1)

    plt.ion()
    fig.show()


if __name__ == '__main__':
    smooth_test()
    input("Press [enter] to continue.")
    print("done")
