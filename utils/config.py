import pyaudio

class Config:

    # Common parameters
    RATE = 44100  # frames per a second
    MESSAGE_SEPARATOR = "---\n"

    # Listener parameters
    
    CHUNK_LENGTH_MS = 5
    FORMAT = pyaudio.paInt16

    # Decoder parameters
    sound_level_threshold = 400
    sound_level_autotune = False
    SNR = 0.7
    THRESHOLD_LOW_LIMIT = 200

    smooth_window_len = 6
    smooth_window_type = 'blackman'
    smooth_cut_off_offset = 0.0

    receiver_wpm = 20
    wpm_variance = 35  # percent
    wpm_autotune = True

    receiver_frequency = 500
    frequency_auto_tune = True
    frequency_variance = 10  # percent

    FREQUENCY_LOW_LIMIT = 100
    FREQUENCY_HIGH_LIMIT = 1000
    frequency_min = int(receiver_frequency * ((100 - frequency_variance) / 100))
    frequency_max = int(receiver_frequency * ((100 + frequency_variance) / 100))

    chunk = int(RATE / 1000 * CHUNK_LENGTH_MS)


    # Keyboard transmitter parameters
    keyboard_transmit_queue_maxsize = 10000
    sender_frequency = 400
    sender_wpm = 20