import numpy as np
from pylsl import StreamInlet, resolve_byprop
import matplotlib.pyplot as plt
from matplotlib.animation import FuncAnimation
from scipy.signal import lfilter, lfilter_zi, firwin

BLINK_SPEED = 1
NUM_POINTS = 512  # Adjusted NUM_POINTS for a larger FFT window
MAX_SAMPLES = 24  # Adjusted MAX_SAMPLES to match the stream's chunk size
SAMPLING_RATE = 256  # Assuming a sampling rate of 256 Hz
FFT_SIZE = 100
GRAPH_SIZE = 1000
DATA_VAR = 0

# Bandpass filter parameters
bf = firwin(32, np.array([1, 40]) / (SAMPLING_RATE / 2.), width=0.05, pass_zero=False)
af = [1.0]
zi = lfilter_zi(bf, af)
filt_state = np.tile(zi, (MAX_SAMPLES, 1)).transpose()
data_f = np.zeros((MAX_SAMPLES, MAX_SAMPLES))

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

d0 = list(np.zeros(GRAPH_SIZE))

fig, (ax, ax_fft) = plt.subplots(2, 1, figsize=(10, 6))
lines0, = ax.plot([], [], label='d' + str(DATA_VAR))
ax.set_xlabel('Index')
ax.set_ylabel('Value')
ax.set_title('Live Plot of d' + str(DATA_VAR))
ax.set_ylim(-2000, 2000)
ax.set_xlim(0, GRAPH_SIZE)

ax_fft.set_xlabel('Frequency (Hz)')
ax_fft.set_ylabel('Magnitude')
ax_fft.set_title('FFT of EEG Data')
ax_fft.set_ylim(0, 50000)  # Set a fixed y-axis limit

def update(frame):
    global d0, filt_state

    data, timestamp = inlet.pull_chunk(timeout=0.05, max_samples=MAX_SAMPLES)
    if timestamp:
        data = np.array(data).T

        d0.extend(list(data[DATA_VAR]))
        d0 = d0[-GRAPH_SIZE:]

        lines0.set_data(np.arange(len(d0)), d0)

        # Apply bandpass filter to the EEG data
        filt_data, filt_state = lfilter(bf, af, data, axis=0, zi=filt_state)
        data_f = np.vstack([data_f, filt_data])
        data_f = data_f[-MAX_SAMPLES:]

        # Use the last 100 data points of d0 for FFT
        fft_data = np.fft.fft(data_f[-FFT_SIZE:], n=NUM_POINTS, axis=0)
        freqs = np.fft.fftfreq(NUM_POINTS, d=1/SAMPLING_RATE)

        # Plot the bar graph for FFT data
        ax_fft.clear()
        ax_fft.bar(freqs, np.abs(fft_data), width=1.5)
        ax_fft.set_ylim(0, 50000)  # Set a fixed y-axis limit

        return lines0, ax_fft

ani = FuncAnimation(fig, update, frames=None, blit=True)
plt.show()
