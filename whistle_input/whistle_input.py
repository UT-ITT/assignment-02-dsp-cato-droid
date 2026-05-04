import sounddevice as sd
import numpy as np
import scipy.fftpack
from pynput.keyboard import Key, Controller

#setup for keyboard presses later
keyboard = Controller()

# Set up audio stream
# reduce chunk size and sampling rate for lower latency
CHUNK_SIZE = 1024 # Number of audio frames per buffer
RATE = 44100 # Audio sampling rate (HZ)
CHANNELS = 1 # Mono audio

#taken from guitar tuner example:
#https://www.chciken.com/digital/signal/processing/2020/05/13/guitar-tuner.html
WINDOW_SIZE = 4410 # window size of the DFT in samples #FIXME 0 weg gemacht, damit es schneller geht
windowSamples = [0 for _ in range(WINDOW_SIZE)]

#count up and down movement in frequencies
last_input_freq = 0
up_counter = 0
down_counter = 0
pause_counter = 0

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
    global last_input_freq, history, up_counter, down_counter, pause_counter
    if status:
        print(status)

    input_freq = get_input_freq(indata)

    #FIXME testing, remove later
    #print(f"input frequency: {input_freq:.1f} Hz")
    #print(f"last/current input frequency: {last_input_freq}/{input_freq}: ")
    if last_input_freq < input_freq:
        up_counter += 1
        pause_counter = 0
        if up_counter == 10: #may need to be adjusted if whistle is significantly longer/shorter than in my test
            keyboard.press(Key.up)
            keyboard.release(Key.up)
            up_counter = 0
    elif last_input_freq > input_freq:
        down_counter += 1
        pause_counter = 0
        if down_counter == 10:#may need to be adjusted if whistle is significantly longer/shorter than in my test
            keyboard.press(Key.down)
            keyboard.release(Key.down)
            down_counter = 0
    elif last_input_freq == input_freq: #reset up and down counters on pause to stop false triggers/noise
        pause_counter += 1
        if pause_counter == 5:
            up_counter = 0
            down_counter = 0
            pause_counter = 0

    if input_freq is not None:
        last_input_freq = input_freq
    else:
        last_input_freq = 0

#open audio input stream
stream = sd.InputStream(
    device=input_device,
    channels=CHANNELS,
    samplerate=RATE,
    blocksize=CHUNK_SIZE,
    callback=audio_callback,
    latency='low'
)

#continously capture audio signal
try:
    with stream:
        print("Press Ctrl+C to stop")
        while True:
            sd.sleep(500)
except KeyboardInterrupt:
    print("\nStopped by user")