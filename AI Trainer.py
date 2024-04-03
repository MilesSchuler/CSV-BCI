import tensorflow as tf
import csv
import numpy as np
import sys
from training_constants import CHUNK_LENGTH, CHUNK_OVERLAP, chunk_generator
from keras.optimizers.schedules import ExponentialDecay
from sklearn.model_selection import train_test_split

# Assuming CHUNK_LENGTH, CHUNK_OVERLAP, and other constants are defined elsewhere

x_train = []
y_train = []

xs = []
ys = []

def convert_labels(arr):
    if [0, 1] in arr:
        return [0, 1]
    return [1, 0]

with open("2024-03-19 10:07:20.144829") as f:  # Make sure to replace 'your_dataset.csv' with your actual file name
    reader = csv.reader(f)
    for row in reader:
        input = [float(row[1]), float(row[2]), float(row[3]), float(row[4])]
        expected = [0, 1] if row[5] == "True" else [1, 0]  # Convert labels to one-hot encoded vectors
        xs.append(input)
        ys.append(expected)

for x, y in zip(chunk_generator(xs, CHUNK_LENGTH, CHUNK_OVERLAP), chunk_generator(ys, CHUNK_LENGTH, CHUNK_OVERLAP)):
    flattened_x = np.array(x).flatten()  # Flatten the input chunk
    x_train.append(flattened_x)
    y_train.append(convert_labels(y))

x_train_real = []
y_train_real = []

for x1, y1 in zip(x_train, y_train):
    if len(x1) == CHUNK_LENGTH * 4:
        x_train_real.append(x1)
        y_train_real.append(y1)

x_train = np.array(x_train_real)
y_train = np.array(y_train_real)

print("THERE ARE " + str(len(x_train)) + " DATA POINTS")

model = tf.keras.models.Sequential([
    tf.keras.layers.Input(shape=(CHUNK_LENGTH * 4,)),
    tf.keras.layers.Dense(256, activation='relu'),
    tf.keras.layers.Dense(256, activation='relu'),
    tf.keras.layers.Dense(64, activation='relu'),
    #tf.keras.layers.Dropout(0.2),  # Increased dropout rate for regularization
    tf.keras.layers.Dense(2, activation='softmax')
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
history = model.fit(x_train, y_train, epochs=25)

# Save the trained model
model.save('data_test_2.keras')

# You can plot the training and validation loss to visualize the overfitting
