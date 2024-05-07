import numpy as np
import matplotlib.pyplot as plt
import csv

# Load data from the CSV file
data_filename = "usingmuselsl/data_2024-05-06_20-49-31.csv"  # Replace with your actual filename
data = np.genfromtxt(data_filename, delimiter=',', skip_header=0)

# Extract timestamps, data, and blink data
timestamps = data[:, 5]  # Assuming timestamps are in the 6th column
data_columns = data[:, :5].T  # Assuming data is in columns 1 to 5
blink_data = data[:, 6]  # Assuming blink data is in the 7th column

# Plot the data
fig, axs = plt.subplots(data_columns.shape[0], 1, figsize=(10, 6), sharex=True)
for i, ax in enumerate(axs):
    # Plot data
    ax.plot(timestamps, data_columns[i])

    # Highlight blinks for all channels
    blink_indices = np.where(blink_data == 1)[0]
    for blink_index in blink_indices:
        ax.plot(timestamps[blink_index], data_columns[i][blink_index], 'ro', markersize=1)  # Set the point to red

    ax.set_ylabel(f"Channel {i+1}")
    ax.grid(True)

plt.xlabel("Time (seconds)")
plt.tight_layout()
plt.show()
