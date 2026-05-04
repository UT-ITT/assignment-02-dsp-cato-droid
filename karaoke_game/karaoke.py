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

#flag for finished midi to stop program
end = False

#scoring
score_hits = 0
score_total = 0


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

#convert frequency to midi note
def freq_to_midi(freq):
    if freq <= 0:
        return None
    return int(round(69 + 12 * np.log2(freq / 440.0)))

#convert midi note to frequency
def midi_to_freq(note):
    return 440 * 2 ** ((note - 69) / 12)


#play midi to compare input to
def midi_player():
    global target_freq, end
    
    for msg in MidiFile('Alle_Meine_Entchen.mid').play():
        if msg.type == "note_on":
            freq = midi_to_freq(msg.note)
            target_freq = freq
    end = True

#calculate moving average over input pitch to smooth out the curve
pitch_history = []
def smooth_pitch(freq):
    pitch_history.append(freq)
    if len(pitch_history) > 5:
        pitch_history.pop(0)
    return np.mean(pitch_history)

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

        return(smooth_pitch(maxFreq))
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

    if target_freq is not None:
        target_freqs.append(target_freq)
    else:
        target_freqs.append(0)


    #score count and continuous freq/diff output
    if target_freq is not None and input_freq is not None:
        target_note = freq_to_midi(target_freq)
        input_note = freq_to_midi(input_freq)

        if target_note is not None and input_note is not None:
            score_total += 1

            if abs(target_note - input_note) < 1:
                score_hits += 1

        diff = input_freq - target_freq
        
        print(f"Target: {target_freq:.1f} Hz | "
              f"You: {input_freq:.1f} Hz | "
              f"Diff: {diff:.1f} Hz")



    #data = indata[:, 0]  # mono
    #curve.setData(data)

def update_plot():
    input_curve.setData(input_freqs)
    target_curve.setData(target_freqs)

    if end:
        print("\nfinal score:")
        if score_total > 0:
            percent = (score_hits / score_total) * 100
            print(f"Accuracy: {percent:.2f}%")
        else:
            print("No valid input detected.")

        pg.QtCore.QTimer.singleShot(500, app.quit)

timer = pg.QtCore.QTimer()
timer.timeout.connect(update_plot)
timer.start(10)  #ca. 10 FPS


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