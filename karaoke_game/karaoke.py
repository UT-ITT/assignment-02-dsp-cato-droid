import sounddevice as sd
import numpy as np
import pyqtgraph as pg
import scipy.fftpack
import threading
import mido
from mido import MidiFile

#freq from midi
target_freq = None

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
target_freqs = [0] * history


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


# set up interactive plot
app = pg.mkQApp("Audio Visualizer")

win = pg.GraphicsLayoutWidget(title="Live Audio")
plot = win.addPlot()
plot.setYRange(0, 1000)

input_curve = plot.plot(pen='b', name="input")
target_curve = plot.plot(pen='r', name="target")

win.show()

#play midi to compare input to
def midi_player():
    global target_freq
    
    for msg in MidiFile('Alle_Meine_Entchen.mid').play():
        if msg.type == "note_on":
            freq = 440 * 2 ** ((msg.note - 69) / 12)
            target_freq = freq

def get_input_freq(indata):
    #some code here adjusted from guitar tuner example: 
    #https://www.chciken.com/digital/signal/processing/2020/05/13/guitar-tuner.html
    global windowSamples
    if any(indata):
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
    global input_freqs, target_freqs, target_freq
    if status:
        print(status)

    input_freq = get_input_freq(indata)

    if input_freq is not None:
        input_freqs.append(input_freq)
    else:
        input_freqs.append(0)

    if target_freq is not None:
        target_freqs.append(target_freq)
    else:
        target_freqs.append(0)



    # if target_freq is not None and input_freq is not None:
    #     diff = input_freq - target_freq
        
    #     print(f"Target: {target_freq:.1f} Hz | "
    #           f"You: {input_freq:.1f} Hz | "
    #           f"Diff: {diff:.1f} Hz")



    #data = indata[:, 0]  # mono
    #curve.setData(data)

def update_plot():
    input_curve.setData(input_freqs)
    target_curve.setData(target_freqs)

timer = pg.QtCore.QTimer()
timer.timeout.connect(update_plot)
timer.start(30)  #ca. 30 FPS


# open audio input stream
stream = sd.InputStream(
    device=input_device,
    channels=CHANNELS,
    samplerate=RATE,
    blocksize=CHUNK_SIZE,
    callback=audio_callback,
    latency='low'
)

#run midi in separate thread
threading.Thread(target=midi_player, daemon=True).start()


# continously capture and plot audio signal
with stream:
    pg.exec()

#TODO
'''
-detect when frequencies match
-count some score
-fix x axis scaling
stop when midi ends
'''