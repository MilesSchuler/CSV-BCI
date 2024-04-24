import tensorflow as tf
import csv
import numpy as np
import sys
from training_constants import CHUNK_LENGTH, CHUNK_OVERLAP, OUTPUT_SIZE, chunk_generator
from keras.optimizers.schedules import ExponentialDecay
from sklearn.model_selection import train_test_split

# Assuming CHUNK_LENGTH, CHUNK_OVERLAP, and other constants are defined elsewhere

x_train = []
y_train = []

xs = []
ys = []

def convert_direction_to_onehot(direction):
    if direction == "up":
        return np.array([1, 0, 0, 0, 0])
    elif direction == "down":
        return np.array([0, 1, 0, 0, 0])
    elif direction == "left":
        return np.array([0, 0, 1, 0, 0])
    elif direction == "right":
        return np.array([0, 0, 0, 1, 0])
    else: # none
        return np.array([0, 0, 0, 0, 1])
    
def convert_labels(arr):
    directions = np.sum(arr, axis=0) / len(arr)
    return directions

with open("Tetris 2024-04-03 14.08.56.673791.csv") as f:  # Make sure to replace 'your_dataset.csv' with your actual file name
    reader = csv.reader(f)
    next(reader, None)
    for row in reader:
        input = [float(row[1]), float(row[2]), float(row[3]), float(row[4])]
        expected = convert_direction_to_onehot(row[5])
        xs.append(input)
        ys.append(expected)

assert len(xs) == len(ys)


for x, y in zip(chunk_generator(xs, CHUNK_LENGTH, CHUNK_OVERLAP), chunk_generator(ys, CHUNK_LENGTH, CHUNK_OVERLAP)):
    #flattened_x = np.array(x).flatten()  # Flatten the input chunk
    x = np.array(x)
    if x.shape == (CHUNK_LENGTH, 4):
        x_train.append(np.array(x))
        y_train.append(convert_labels(y))

assert len(x_train) == len(y_train)

print(y_train[0])

print("THERE ARE " + str(len(x_train)) + " DATA POINTS")

model = tf.keras.models.Sequential([
    tf.keras.layers.Input(shape=(CHUNK_LENGTH, 4)),
    tf.keras.layers.Flatten(),  # This layer flattens the input sequence
    tf.keras.layers.Dense(256, activation='relu'),
    tf.keras.layers.Dense(256, activation='relu'),
    tf.keras.layers.Dense(64, activation='relu'),
    tf.keras.layers.Dropout(0.2),
    tf.keras.layers.Dense(OUTPUT_SIZE, activation='softmax')
])


initial_learning_rate = 0.0005
decay_rate = 0.90

lr_scheduler = ExponentialDecay(
    initial_learning_rate, 
    decay_steps=10000, 
    decay_rate=decay_rate, 
    staircase=True
)


model.compile(optimizer=tf.keras.optimizers.Adam(learning_rate=lr_scheduler),
              loss='categorical_crossentropy',
              metrics=['accuracy'])

# Train the model with validation split
history = model.fit(np.array(x_train), np.array(y_train), epochs=25)

# Save the trained model
model.save('data_test_2.keras')

# You can plot the training and validation loss to visualize the overfitting
