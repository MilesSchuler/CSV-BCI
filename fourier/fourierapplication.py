import numpy as np
import pandas as pd
import random
from time import time, strftime, gmtime
from optparse import OptionParser
from pylsl import StreamInlet, resolve_byprop

BLINK_SPEED = 1
NUM_POINTS = 24
MAX_SAMPLES = 12
SAMPLING_RATE = 256  # Assuming a sampling rate of 256 Hz

default_fname = ("data/data_%s.csv" % strftime("%Y-%m-%d-%H.%M.%S", gmtime()))

parser = OptionParser()
parser.add_option("-f", "--filename",
                  dest="filename", type='str', default=default_fname,
                  help="Name of the recording file.")
(options, args) = parser.parse_args()

print("looking for an EEG stream...")
streams = resolve_byprop('type', 'EEG', timeout=2)
if len(streams) == 0:
    raise Exception("Can't find EEG stream")
print("Start acquiring data")
inlet = StreamInlet(streams[0], max_chunklen=12)
eeg_time_correction = inlet.time_correction()
print("looking for a Markers stream...")
marker_streams = resolve_byprop('type', 'Markers', timeout=2)
if marker_streams:
    inlet_marker = StreamInlet(marker_streams[0])
    marker_time_correction = inlet_marker.time_correction()
else:
    inlet_marker = False
    print("Can't find Markers stream")

currentWord = 1
currentTerm = "foo"
t_word = time() + BLINK_SPEED
res = []
words = []

t_init = time()
print('Start recording at time t=%.3f' % t_init)
print(currentTerm)

try:
    while True:
        # Check for new word
        if time() >= t_word:
            currentTerm = random.choice(["foo", "bar", "baz"])  # feel free to use your own!
            print("\n \n \n \n \n \n \n \n \n \n \n \n \n \n \n \n \n \n \n \n \n \n \n" + str(
                currentWord) + ": " + currentTerm)
            currentWord += 1
            t_word = time() + BLINK_SPEED

        # Pull data from the EEG device every 100 milliseconds
        data, timestamp = inlet.pull_chunk(timeout=0.1, max_samples=MAX_SAMPLES)
        if timestamp:
            # Perform FFT on the data
            fft_data = np.fft.fft(data, n=NUM_POINTS, axis=0)
            # Calculate the corresponding frequencies
            freqs = np.fft.fftfreq(NUM_POINTS, d=1/SAMPLING_RATE)
            res.append(fft_data)
            # Extend words to match the number of FFT bins
            words.extend([currentTerm] * fft_data.shape[1])
except KeyboardInterrupt:
    pass

res = np.concatenate(res, axis=1).T

# Combine all data into a DataFrame
print(len(words))
print(len(res))

data = pd.DataFrame({
    'words': words,
    **{f'fft_{freqs[i]:.2f}Hz': res[:, i] for i in range(res.shape[1])}
})

# Save the data to a CSV file
data.to_csv(options.filename, float_format='%.3f', index=False)
print('Done!')
print(default_fname)
