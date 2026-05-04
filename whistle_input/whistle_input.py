import sounddevice as sd
import numpy as np
import pyqtgraph as pg
import scipy.fftpack
import pygame

# Set up audio stream
# reduce chunk size and sampling rate for lower latency
CHUNK_SIZE = 1024 # Number of audio frames per buffer
RATE = 44100 # Audio sampling rate (HZ)
CHANNELS = 1 # Mono audio

#taken from guitar tuner example:
#https://www.chciken.com/digital/signal/processing/2020/05/13/guitar-tuner.html
WINDOW_SIZE = 4410 # window size of the DFT in samples #FIXME 0 weg gemacht, damit es schneller geht
windowSamples = [0 for _ in range(WINDOW_SIZE)]

#frequency buffers
history = 200  # number of points on screen

input_freqs = [0] * history

# print info about audio devices
print("Available input devices:\n")
devices = sd.query_devices()

input_devices = []
for i, dev in enumerate(devices):
    if dev['max_input_channels'] > 0:
        print(f"{i}: {dev['name']}")
        input_devices.append(i)

# let user select audio device
input_device = int(input("\nSelect input device: "))


#extract the main input (singig) frequency
def get_input_freq(indata):
    #some code here adjusted from guitar tuner example: 
    #https://www.chciken.com/digital/signal/processing/2020/05/13/guitar-tuner.html
    global windowSamples
    if any(indata):
        if np.linalg.norm(indata[:, 0]) < 0.1: #ignore low-volume noise
            return None
        windowSamples = np.concatenate((windowSamples,indata[:, 0])) # append new samples
        windowSamples = windowSamples[len(indata[:, 0]):] # remove old samples
        magnitudeSpec = abs( scipy.fftpack.fft(windowSamples)[:len(windowSamples)//2] )

        for i in range(int(62/(RATE/WINDOW_SIZE))):
            magnitudeSpec[i] = 0 #suppress mains hum

        maxInd = np.argmax(magnitudeSpec)
        maxFreq = maxInd * (RATE/WINDOW_SIZE)

        return(maxFreq)
        print(f"Main Frequency: {maxFreq:.1f}")
    else:
        print('no input')
        return(None)


# audio callback to safe data
def audio_callback(indata, frames, time, status):
    global input_freqs, target_freqs, target_freq, score_hits, score_total
    if status:
        print(status)

    input_freq = get_input_freq(indata)

    if input_freq is not None:
        input_freqs.append(input_freq)
    else:
        input_freqs.append(0)

    #FIXME testing, remove later
    print(f"input frequency: {input_freq:.1f} Hz")
    print(f"input frequencies: {input_freqs}")

    #FIXME check if at least 5 (or more?) frequency entries in list are going up/down and trigger event


# open audio input stream
stream = sd.InputStream(
    device=input_device,
    channels=CHANNELS,
    samplerate=RATE,
    blocksize=CHUNK_SIZE,
    callback=audio_callback,
    latency='low'
)

# continously capture and print audio signal
try:
    with stream:
        print("Press Ctrl+C to stop")
        while True:
            sd.sleep(500)
except KeyboardInterrupt:
    print("\nStopped by user")