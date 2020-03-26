#!/usr/bin/python3
import pygame
from pygame.mixer import Sound, get_init, pre_init
from array import array
import time

class ToneSound(pygame.mixer.Sound):
    frequency = 500
    volume = 0.5

    def __init__(self):

        pygame.mixer.pre_init(44100, -16, 1, 1024)
        #pygame.init()
        #pygame.mixer.Sound.__init__(self, self.build_samples())

    def build_samples(self):
        period = int(round(pygame.mixer.get_init()[0] / self.frequency))
        samples = array("h", [0] * period)
        amplitude = 2 ** (abs(pygame.mixer.get_init()[1]) - 1) - 1
        for time in range(period):
            if time < period / 2:
                samples[time] = amplitude
            else:
                samples[time] = -amplitude
        return samples

    def start_beep(self):
        self.play(-1) #the -1 means to loop the sound

    def stop_beep(self):
        self.stop() 