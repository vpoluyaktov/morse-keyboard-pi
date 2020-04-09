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
dash_duration = 0.3
dit_duration = 0.05

# envelope N ms raised cosine 
attack_release_ms = 20
attack_release_frames = fs*dit_duration*attack_release_ms/1000  

samples_dit = (np.sin(2*np.pi*np.arange(fs*dit_duration)*f/fs)).astype(np.float32) * volume

attack_curve = np.arange(0, 1, 1/attack_release_frames)
release_curve = np.arange(1, 0, -1/attack_release_frames)
envelope_plate = np.repeat(1, fs*dit_duration - (attack_release_frames*2))
envelope = np.concatenate((attack_curve, envelope_plate, release_curve))

samples_dit = samples_dit * envelope[:len(samples_dit)]


axes = plt.gca()
axes.set_ylim(ymin=-1, ymax=1)
plt.axhline(0)
plt.plot(samples_dit)
plt.plot(envelope)

plt.show()