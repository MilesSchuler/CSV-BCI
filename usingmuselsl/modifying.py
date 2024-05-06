import numpy as np
import matplotlib.pyplot as plt
from matplotlib.animation import FuncAnimation
from scipy.signal import lfilter, lfilter_zi, firwin
from time import sleep
from pylsl import StreamInlet, resolve_byprop
from threading import Thread

MAX_SAMPLES = 24
WINDOW_SIZE = 5
DEJITTER = True
started = False

# find stream
print("looking for an EEG stream...")
streams = resolve_byprop('type', 'EEG', timeout=2)
if len(streams) == 0:
    raise Exception("Can't find EEG stream")
print("Start acquiring data")
inlet = StreamInlet(streams[0], max_chunklen=MAX_SAMPLES)
eeg_time_correction = inlet.time_correction()
print("looking for a Markers stream...")
marker_streams = resolve_byprop('type', 'Markers', timeout=2)
if marker_streams:
    inlet_marker = StreamInlet(marker_streams[0])
    marker_time_correction = inlet_marker.time_correction()
else:
    inlet_marker = False
    print("Can't find Markers stream")


# get basic information
info = inlet.info()
SAMPLING_FREQUENCY = info.nominal_srate(); assert SAMPLING_FREQUENCY == 256
SAMPLES_COUNT = int(SAMPLING_FREQUENCY * WINDOW_SIZE)
CHANNELS_COUNT = info.channel_count()

# bandpass filter from 1 Hz to 40 Hz (i don't really understand this)
BANDPASS_FILTER = firwin(32, np.array([1, 40]) / (SAMPLING_FREQUENCY / 2.), width=0.05, pass_zero=False)
FEEDBACK_COEFFICIENTS = [1.0]
INITIAL_FILTER = lfilter_zi(BANDPASS_FILTER, FEEDBACK_COEFFICIENTS)
filter_state = np.tile(INITIAL_FILTER, (CHANNELS_COUNT, 1)).transpose()

# set up lists for data streams
times = np.arange(-WINDOW_SIZE, 0, 1/SAMPLING_FREQUENCY)
data = np.zeros((SAMPLES_COUNT, CHANNELS_COUNT))
data_filtered = np.zeros((SAMPLES_COUNT, CHANNELS_COUNT))

def get_data():
    global SAMPLES_COUNT, filter_state, times, data, data_filtered

    while started:
        samples, timestamps = inlet.pull_chunk(timeout=0.05, max_samples=MAX_SAMPLES)
        if timestamps:
            if DEJITTER:
                timestamps = np.float64(np.arange(len(timestamps)))
                timestamps /= SAMPLING_FREQUENCY
                timestamps += times[-1] + 1. / SAMPLING_FREQUENCY

            # add new timestamps to times list
            times = np.concatenate([times, np.atleast_1d(timestamps)])
            SAMPLES_COUNT = int(SAMPLING_FREQUENCY * WINDOW_SIZE)
            # remove old timestamps from the front of times
            times = times[-SAMPLES_COUNT:]

            # add new samples to data list
            data = np.vstack([data, samples])
            # remove old samples from the fromt of data
            data = data[-SAMPLES_COUNT:]

            # filter out noise
            filt_samples, filter_state = lfilter(BANDPASS_FILTER, FEEDBACK_COEFFICIENTS, samples, axis=0, zi=filter_state)
            # add new filtered data to data_filtered
            data_filtered = np.vstack([data_filtered, filt_samples])
            # remove old filtered data from the fromt of data_filtered
            data_filtered = data_filtered[-SAMPLES_COUNT:]
        else:
            sleep(0.2)

def start():
    global started
    started = True
    thread = Thread(target=get_data)
    thread.daemon = True
    thread.start()

def stop():
    global started
    started = False

print("Starting...")
start()

fig, axs = plt.subplots(CHANNELS_COUNT, 1, figsize=(10, 6))
plt.tight_layout()

def update_plot(i):
    for ax in axs:
        ax.clear()
    for i, ax in enumerate(axs):
        ax.plot(times, np.transpose(data_filtered)[i])

ani = FuncAnimation(fig, update_plot, interval=200)
plt.show()

"""
while True:
    try:
        sleep(1)
        print(data_filtered)
    except KeyboardInterrupt:
        print("\nStopping...")
        started = False
        break
"""