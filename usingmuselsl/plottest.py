import numpy as np
import matplotlib.pyplot as plt
from matplotlib.animation import FuncAnimation

# Sample data
data = [['a', 'b', 'c', 'd', 'e'],
        ['f', 'g', 'h', 'i', 'j'],
        ['k', 'l', 'm', 'n', 'o']]

# Convert data to a NumPy array
data_array = np.array(data)

# Create a figure and subplots with adjusted heights
fig, axs = plt.subplots(5, 1, figsize=(10, 8), gridspec_kw={'height_ratios': [1, 1, 1, 1, 1]})

# Setting the axis labels and limits
for ax in axs:
    ax.set_xlabel('Index')
    ax.set_ylabel('Letter Value (a=0, b=1, ..., e=4)')


lines = [ax.plot([], [])[0] for ax in axs]

# Update function for animation
def update(frame):
    for i, line in enumerate(lines):
        line.set_data(range(data_array.shape[0]), [ord(data_array[j, i]) - ord('a') for j in range(data_array.shape[0])])
    return lines

# Create the animation
ani = FuncAnimation(fig, update, frames=range(data_array.shape[1]), interval=1000)

plt.tight_layout()
plt.show()
