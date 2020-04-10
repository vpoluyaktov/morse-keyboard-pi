#!/usr/bin/env python

import numpy as np
import pyaudio  
import time
import matplotlib.pyplot as plt

p = pyaudio.PyAudio()

volume = 0.5     # range [0.0, 1.0]
fs = 44100       # sampling rate, Hz, must be integer
duration = 0.3   # in seconds, may be float
f = 652.0        # sine frequency, Hz, may be float

# generate samples
dah_duration = 0.15
dit_duration = 0.05

# envelope N ms raised cosine 
attack_release_ms = 50

samples_dit = (np.sin(2*np.pi*np.arange(fs*dit_duration)*f/fs)).astype(np.float32) * volume
samples_dah = (np.sin(2*np.pi*np.arange(fs*dah_duration)*f/fs)).astype(np.float32) * volume
samples_char_space = (np.sin(2*np.pi*np.arange(fs*dit_duration)*0/fs)).astype(np.float32) * volume
samples_letter_space = (np.sin(2*np.pi*np.arange(fs*dit_duration*3)*0/fs)).astype(np.float32) * volume
samples_word_space = (np.sin(2*np.pi*np.arange(fs*dit_duration*7)*0/fs)).astype(np.float32) * volume

# apply raised cosine envelope
attack_release_frames = fs*dit_duration*attack_release_ms/1000  
attack_curve = np.arange(0, 1, 1/attack_release_frames, dtype=np.float32)
release_curve = np.arange(1, 0, -1/attack_release_frames, dtype=np.float32)
envelope_dit_plate = np.repeat(np.float32(1), fs*dit_duration - (attack_release_frames*2))
envelope_dit = np.concatenate((attack_curve, envelope_dit_plate, release_curve))
envelope_dah_plate = np.repeat(np.float32(1), fs*dah_duration - (attack_release_frames*2))
envelope_dah = np.concatenate((attack_curve, envelope_dah_plate, release_curve))

samples_dit = samples_dit * envelope_dit[:len(samples_dit)]
samples_dah = samples_dah * envelope_dah[:len(samples_dah)]

axes = plt.gca()
axes.set_ylim(ymin=-1, ymax=1)
plt.axhline(0)
plt.plot(samples_dit)
plt.plot(envelope_dit*volume, linewidth=1, color='r', linestyle='dotted')
plt.show()

# for paFloat32 sample values must be in range [-1.0, 1.0]
stream = p.open(format=pyaudio.paFloat32,
                channels=1,
                rate=fs,
                output=True)


char_samples = np.empty([0],dtype=np.float32)
char_samples = np.concatenate((char_samples, samples_dit))
char_samples = np.concatenate((char_samples, samples_char_space))
char_samples = np.concatenate((char_samples, samples_dah))
char_samples = np.concatenate((char_samples, samples_char_space))
char_samples = np.concatenate((char_samples, samples_dit))
char_samples = np.concatenate((char_samples, samples_char_space))
char_samples = np.concatenate((char_samples, samples_dit))
char_samples = np.concatenate((char_samples, samples_letter_space))

while True:
    stream.write(char_samples, len(char_samples))


stream.stop_stream()
stream.close()

p.terminate()
