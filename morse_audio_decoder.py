#!/usr/bin/python3

from sys import byteorder
from array import array
from struct import pack

import pyaudio
import wave
import struct
import numpy as np

WPS = 20
WPS_VARIANCE = 20 #  10 persents
FREQ = 650
HzVARIANCE = 20
THRESHOLD = 300

RATE = 48000  # frames per a second
CHUNK_LENGTH_MS = 10  
FORMAT = pyaudio.paInt16
ALLOWANCE = 3

chunk = int(RATE / 1000 * CHUNK_LENGTH_MS)
window = np.blackman(chunk)

# morse code timing
dit_length_ms = int(1200 / WPS)
dah_length_ms = dit_length_ms * 3
char_space_length_ms = dit_length_ms
letter_space_length_ms = dit_length_ms * 3
word_space_length_ms = dit_length_ms * 7

# morse code timing variances in frames
dit_length_min = int(dit_length_ms * ((100 - WPS_VARIANCE) / 100) / CHUNK_LENGTH_MS)
dit_length_max = int(dit_length_ms * ((100 + WPS_VARIANCE) / 100) / CHUNK_LENGTH_MS)
dah_length_min = dit_length_min * 3
dah_length_max = dit_length_max * 3
char_space_length_min = dit_length_min
char_space_length_max = dit_length_max
letter_space_length_min = dit_length_min * 3
letter_space_length_max = dit_length_max * 3
word_space_length_min = dit_length_min * 7
word_space_length_max = dit_length_max * 7

print(dit_length_ms, dit_length_min, dit_length_max)
print(dah_length_ms, dah_length_min, dah_length_max)
print(char_space_length_min, char_space_length_max)
print(letter_space_length_min, letter_space_length_max)
print(word_space_length_min, word_space_length_max)

WINDOW = word_space_length_min

letter_to_morse = {
	"a" : ".-",	"b" : "-...",	"c" : "-.-.",
	"d" : "-..",	"e" : ".",	"f" : "..-.",
	"g" : "--.",	"h" : "....",	"i" : "..",
	"j" : ".---",	"k" : "-.-",	"l" : ".-..",
	"m" : "--",	"n" : "-.",	"o" : "---",
	"p" : ".--.",	"q" : "--.-",	"r" : ".-.",
	"s" : "...",	"t" : "-",	"u" : "..-",
	"v" : "...-",	"w" : ".--",	"x" : "-..-",
	"y" : "-.--",	"z" : "--..",	"1" : ".----",
	"2" : "..---",	"3" : "...--",	"4" : "....-",
	"5" : ".....", 	"6" : "-....",	"7" : "--...",
	"8" : "---..",	"9" : "----.",	"0" : "-----",	
	" " : "/"}

def is_silent(snd_data):
    "Returns 'True' if below the 'silent' threshold"
    return max(snd_data) < THRESHOLD

def normalize(snd_data):
    "Average the volume out"
    #32768 maximum /2
    MAXIMUM = 16384
    times = float(MAXIMUM)/max(abs(i) for i in snd_data)

    r = array('h')
    for i in snd_data:
        r.append(int(i*times))
    return r

def encode(list1):
    
    list1=list1.split("0")
    listascii=""
    counter=0

    for i in range(len(list1)):
        if len(list1[i])==0: #blank character adds 1
            counter+=1
        else:
            if counter < ALLOWANCE:
                list1[i] += list1[i-counter-1]
                list1[i-counter-1] = ""
            counter=0
    # print(list1); 

    for i in range(len(list1)):
        # print(len(list1[i]), dit_length_min, dit_length_max)
        if dit_length_min <= len(list1[i]) < dit_length_max:
            listascii+="."
            counter=0
        elif dah_length_min <= len(list1[i]) < dah_length_max:
            listascii+="-"
            counter=0
        elif len(list1[i])==0: #blank character adds 1
            counter+=1
            if char_space_length_min < counter < char_space_length_max and i < (len(list1) - 1) and len(list1[i+1]) != 0: 
                #listascii+=""
                counter=0
            elif counter >= word_space_length_min:
                listascii+=" "
                counter=0
                
    #print(listascii)
    listascii=listascii.split(" ")

    stringout=""
   
    print(listascii)
    for i in range(len(listascii)):
        for letter,morse in letter_to_morse.items():
            if listascii[i]==morse:
                stringout+=letter
        if listascii[i]=="":
            stringout+=" "

    if(stringout!= " "):
        print(stringout, end = '')
    
    #print("record start")
    #record()
    
def record():
    num_silent = 0
    snd_started = False
    oncount = 0
    offcount = 0
    status = 0
    timelist = ""

    p = pyaudio.PyAudio()
    stream = p.open(format=FORMAT, 
			channels=1, 
			rate=RATE,
        		input=True, 
			input_device_index=2, 
			frames_per_buffer=chunk)


    #r = array('h')
    print("started")
    while True:
        

        snd_data = stream.read(chunk, exception_on_overflow = False)

        if byteorder == 'big':
            snd_data.byteswap()

        #r.extend(snd_data)
        sample_width = p.get_sample_size(FORMAT)

        #find frequency of each chunk
        indata = np.array(wave.struct.unpack("%dh"%(chunk), snd_data))*window

        #take fft and square each value
        fftData = abs(np.fft.rfft(indata))**2

        # find the maximum
        which = fftData[1:].argmax() + 1
        silent = is_silent(indata)
        
        if silent:
            thefreq = 0
        elif which != len(fftData)-1:
            y0,y1,y2 = np.log(fftData[which-1:which+2:])
            x1 = (y2 - y0) * .5 / (2 * y1 - y2 - y0)
            # find the frequency and output it
            thefreq = (which+x1)*RATE/chunk
        else:
            thefreq = which*RATE/chunk
        # print(thefreq)
        
        if thefreq > (FREQ-HzVARIANCE) and thefreq < (FREQ+HzVARIANCE):
            status = 1
            # print("1")
        else:
            status = 0
            # print("0")
            
        if status == 1:
            timelist+="1"
            num_silent = 0
            
        else:
            timelist+="0"
            num_silent += 1
            
        # print(timelist)
        # print(num_silent)

        if num_silent > WINDOW and "1" in timelist:
            #print(timelist)
            #print("\n")
            #stream.stop_stream()
            #stream.close()
            encode(timelist)
            timelist=""

        if num_silent > 1000:
            print("reset")
            num_silent =0
        
    #print (timelist)
    print("ended")
    # print(num_silent)
    p.terminate()

record()
