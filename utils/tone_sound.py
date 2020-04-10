#!/usr/bin/env python

import numpy as np
import pyaudio
import time
import matplotlib.pyplot as plt


class ToneSounder:

    volume = 0.5     # range [0.0, 1.0]
    fs = 44100       # sampling rate, Hz
    f = 650.0        # sine frequency, Hz

    # envelope N ms raised cosine
    attack_release_ms = 50

    def __init__(self):
        self.p = pyaudio.PyAudio()
        # for paFloat32 sample values must be in range [-1.0, 1.0]
        self.stream = self.p.open(format=pyaudio.paFloat32,
                             channels=1,
                             rate=self.fs,
                             output=True)

        # generate samples
        self.calcualate_timings()
        self.generate_samples()

    def calcualate_timings(self):
        self.wpm = 40
        self.dah_dot_ratio = 3
        self.dit_duration_ms = int(1200 / self.wpm)
        self.dah_duration_ms = self.dit_duration_ms * self.dah_dot_ratio

    def generate_samples(self):

        self.samples_dit = (np.sin(2 * np.pi * np.arange(self.fs * self.dit_duration_ms/1000)
                                   * self.f / self.fs)).astype(np.float32) * self.volume
        self.samples_dah = (np.sin(2 * np.pi * np.arange(self.fs * self.dah_duration_ms/1000)
                                   * self.f / self.fs)).astype(np.float32) * self.volume

        self.samples_char_space = (np.sin(2*np.pi*np.arange(self.fs*self.dit_duration_ms/1000)*0/self.fs)).astype(np.float32)
        self.samples_letter_space = (np.sin(2*np.pi*np.arange(self.fs*self.dit_duration_ms/1000*3)*0/self.fs)).astype(np.float32)
        self.samples_word_space = (np.sin(2*np.pi*np.arange(self.fs*self.dit_duration_ms/1000*7)*0/self.fs)).astype(np.float32)     

        # apply raised cosine envelope
        attack_release_frames = self.fs * self.dit_duration_ms/1000 * self.attack_release_ms / 1000
        attack_curve = np.arange(
            0, 1, 1/attack_release_frames, dtype=np.float32)
        release_curve = np.arange(
            1, 0, -1/attack_release_frames, dtype=np.float32)

        envelope_dit_plate = np.repeat(np.float32(
            1), self.fs * self.dit_duration_ms/1000 - (attack_release_frames * 2) + 2)
        self.envelope_dit = np.concatenate(
            (attack_curve, envelope_dit_plate, release_curve))
        envelope_dah_plate = np.repeat(np.float32(
            1), self.fs * self.dah_duration_ms/1000 - (attack_release_frames * 2) + 2)
        self.envelope_dah = np.concatenate(
            (attack_curve, envelope_dah_plate, release_curve))

        # correct arrays length
        self.samples_dit = self.samples_dit * \
            self.envelope_dit[:len(self.samples_dit)]
        self.samples_dah = self.samples_dah * \
            self.envelope_dah[:len(self.samples_dah)]

    def plot_sample(self):
        axes = plt.gca()
        axes.set_ylim(ymin=-1, ymax=1)
        plt.axhline(0)
        plt.plot(self.samples_dit)
        plt.plot(self.envelope_dit * self.volume,
                 linewidth=1, color='r', linestyle='dotted')
        plt.show()

    def play_dit(self):
        self.stream.write(self.samples_dit)

    def play_dah(self):
        self.stream.write(self.samples_dah)

    def play_char(self, char):
        char_samples = np.empty([0],dtype=np.float32)
        char_samples = np.concatenate((char_samples, self.samples_dit))
        char_samples = np.concatenate((char_samples, self.samples_char_space))
        char_samples = np.concatenate((char_samples, self.samples_dah))
        char_samples = np.concatenate((char_samples, self.samples_char_space))
        char_samples = np.concatenate((char_samples, self.samples_dit))
        char_samples = np.concatenate((char_samples, self.samples_char_space))
        char_samples = np.concatenate((char_samples, self.samples_dit))
        char_samples = np.concatenate((char_samples, self.samples_letter_space))
        self.stream.write(char_samples, len(char_samples))

    def destroy(self):
        self.stream.stop_stream()
        self.stream.close()
        self.p.terminate()
