import matplotlib.pyplot as plt
import numpy as np
from muse2 import Muse

# Initialize Muse2 device
muse = Muse()

# Connect to Muse2
muse.connect()

# Set up plot
plt.ion()
fig, ax = plt.subplots()
x = np.linspace(0, 1, 100)
line, = ax.plot(x, np.zeros_like(x))

# Main loop for real-time plotting
while True:
    # Read data from Muse2
    data = muse.get_data()
    if data is not None:
        # Perform FFT
        fft_data = np.fft.fft(data)
        fft_freq = np.fft.fftfreq(len(data), 1.0 / muse.sampling_rate)
        
        # Update plot
        line.set_ydata(np.abs(fft_data))
        line.set_xdata(fft_freq)
        ax.relim()
        ax.autoscale_view()
        fig.canvas.draw()
        fig.canvas.flush_events()
