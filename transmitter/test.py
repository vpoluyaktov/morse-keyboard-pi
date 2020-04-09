import numpy as np
import pyaudio  
import time

p = pyaudio.PyAudio()

volume = 0.5     # range [0.0, 1.0]
fs = 44100       # sampling rate, Hz, must be integer
duration = 0.3   # in seconds, may be float
f = 650.0        # sine frequency, Hz, may be float

# generate samples
dash_duration = 0.3
dit_duration = 0.1

samples_dit = (np.sin(2*np.pi*np.arange(fs*dit_duration)*f/fs)).astype(np.float32) * volume
samples_dash = (np.sin(2*np.pi*np.arange(fs*dash_duration)*f/fs)).astype(np.float32) * volume
samples_char_space = (np.sin(2*np.pi*np.arange(fs*dit_duration)*0/fs)).astype(np.float32) * volume
samples_letter_space = (np.sin(2*np.pi*np.arange(fs*dit_duration*3)*0/fs)).astype(np.float32) * volume
samples_word_space = (np.sin(2*np.pi*np.arange(fs*dit_duration*7)*0/fs)).astype(np.float32) * volume

# for paFloat32 sample values must be in range [-1.0, 1.0]
stream = p.open(format=pyaudio.paFloat32,
                channels=1,
                rate=fs,
                output=True)

# 
char_samples = np.empty([0],dtype=np.float32)
char_samples = np.concatenate((char_samples, samples_dit))
char_samples = np.concatenate((char_samples, samples_char_space))
char_samples = np.concatenate((char_samples, samples_dash))
char_samples = np.concatenate((char_samples, samples_char_space))
char_samples = np.concatenate((char_samples, samples_dit))
char_samples = np.concatenate((char_samples, samples_char_space))
char_samples = np.concatenate((char_samples, samples_dit))
char_samples = np.concatenate((char_samples, samples_letter_space))

stream.write(char_samples, len(char_samples))


stream.stop_stream()
stream.close()

p.terminate()
