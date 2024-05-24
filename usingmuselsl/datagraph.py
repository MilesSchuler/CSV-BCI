import numpy as np
import matplotlib.pyplot as plt
from matplotlib.animation import FuncAnimation
from scipy.signal import lfilter, lfilter_zi, firwin
from training_constants import CHUNK_LENGTH, BLINK_THRESHOLD
from time import sleep
from pylsl import StreamInlet, resolve_byprop
from threading import Thread
from time import gmtime, strftime
import csv
import os
import tensorflow as tf

MAX_SAMPLES = 24
WINDOW_SIZE = 5
BLINK_RADIUS = 0.25
DEJITTER = True
FILENAME = "usingmuselsl/filtered_data_" + strftime("%Y-%m-%d_%H-%M-%S", gmtime()) + ".csv"
started = False
 
DATA_COLLECTION = False

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
    global SAMPLES_COUNT, filter_state, times, data, data_filtered, ai_blink_timestamps

    if DATA_COLLECTION:
        f = open(FILENAME, 'a')
    else:
        model = tf.keras.models.load_model('usingmuselsl/epic_ai_v12.keras')

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

            if DATA_COLLECTION:
                # add filtered data to csv file
                samples_and_timestamps = np.hstack((filt_samples, timestamps.reshape(-1, 1)))
                np.savetxt(f, samples_and_timestamps, delimiter=',', fmt='%.10f')

            # add new filtered data to data_filtered
            data_filtered = np.vstack([data_filtered, filt_samples])
            # remove old filtered data from the front of data_filtered
            data_filtered = data_filtered[-SAMPLES_COUNT:]

            if not DATA_COLLECTION:
                # evaluate AI
                data = data_filtered[-CHUNK_LENGTH:]
                data_truncated = np.delete(data, -1, axis=1)

                prediction = model.predict(np.array([data_truncated]), verbose=2)
                print(prediction)

                if prediction[0][0] >= BLINK_THRESHOLD:
                    # adjust for delay
                    ai_blink_timestamps.append(times[-1] - 0.25)
        else:
            sleep(0.2)
    if DATA_COLLECTION:
        f.close()

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

# code to log blinks when space is pressed
blink_timestamps = []
ai_blink_timestamps = []

def on_key_press(event):
    if event.key == ' ':
        blink_timestamps.append(times[-1])  # Mark the current timestamp as a blink

fig.canvas.mpl_connect('key_press_event', on_key_press)

def update_plot(i):
    for ax in axs:
        ax.clear()
    for i, ax in enumerate(axs):
        ax.plot(times, np.transpose(data_filtered)[i])

        # filter blink_timestamps to include only those within the current window
        if DATA_COLLECTION:
            blink_times_in_window = [blink_time for blink_time in blink_timestamps if times[-1] - WINDOW_SIZE <= blink_time <= times[-1]]
            for blink_time in blink_times_in_window:
                ax.axvspan(blink_time - BLINK_RADIUS * 0.5, blink_time + BLINK_RADIUS * 1.5, color='red', alpha=0.3)
        else:
            blink_times_in_window = [blink_time for blink_time in ai_blink_timestamps if times[-1] - WINDOW_SIZE <= blink_time <= times[-1]]
            for blink_time in blink_times_in_window:
                ax.axvspan(blink_time - BLINK_RADIUS * 0.5, blink_time + BLINK_RADIUS * 1.5, color='red', alpha=0.3)

ani = FuncAnimation(fig, update_plot, interval=200, save_count=100)
plt.show()

stop()

blink_ranges = [(blink_time - BLINK_RADIUS * 0.5, blink_time + BLINK_RADIUS * 1.5) for blink_time in blink_timestamps]

# inefficient way to mark as blinks
if DATA_COLLECTION:
    NEW_FILENAME = "usingmuselsl/data_" + strftime("%Y-%m-%d_%H-%M-%S", gmtime()) + ".csv"

    with open(FILENAME, 'r', newline='') as file:
        with open(NEW_FILENAME, 'w', newline='') as new_file:
            reader = csv.reader(file)
            writer = csv.writer(new_file)
            
            for row in reader:
                found = False
                for blink_range in blink_ranges:
                    if float(row[5]) >= blink_range[0] and float(row[5]) <= blink_range[1]:
                        row.append("1")
                        found = True
                        break
                if not found:
                    row.append("0")
                writer.writerow(row)

    print("Updated data saved to", NEW_FILENAME)
    os.remove(FILENAME)
    print("Original file deleted")