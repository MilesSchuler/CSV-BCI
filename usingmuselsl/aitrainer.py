import tensorflow as tf
import csv
import numpy as np
import sys
from training_constants import CHUNK_LENGTH, CHUNK_OVERLAP,BLINK_LABEL_COUNT, chunk_generator
from keras.optimizers.schedules import ExponentialDecay
from sklearn.model_selection import train_test_split

# Assuming CHUNK_LENGTH, CHUNK_OVERLAP, and other constants are defined elsewhere

data_x = []
data_y = []

train_x = []
train_y = []

def convert_labels(y_chunk):
    blink_counter = 0
    for y in y_chunk:
        if y == 1.:
            blink_counter += 1
    if blink_counter >= BLINK_LABEL_COUNT:
        return 1.
    else:
        return 0.

with open("usingmuselsl/merged_data.csv") as f:  # Make sure to replace 'your_dataset.csv' with your actual file name
    reader = csv.reader(f)
    # next(reader, None)
    for row in reader:
        data_x.append([float(row[0]), float(row[1]), float(row[2]), float(row[3])])
        data_y.append(float(row[6]))

assert len(data_x) == len(data_y)

for x_chunk, y_chunk in zip(chunk_generator(data_x, CHUNK_LENGTH, CHUNK_OVERLAP), chunk_generator(data_y, CHUNK_LENGTH, CHUNK_OVERLAP)):
    if len(x_chunk) == CHUNK_LENGTH:
        train_x.append(np.array(x_chunk))
        train_y.append(convert_labels(y_chunk))

assert len(train_x) == len(train_y)

print("THERE ARE " + str(len(train_x)) + " DATA POINTS")
print("THERE ARE " + str(np.count_nonzero(train_y)) + " BLINK POINTS")
print("THERE ARE " + str(len(train_y) - np.count_nonzero(train_y)) + " NOBLINK POINTS")

input("Press Enter to continue")

model = tf.keras.models.Sequential([
    tf.keras.layers.Input(shape=(CHUNK_LENGTH, 4)),
    tf.keras.layers.Flatten(),  # This layer flattens the input sequence
    tf.keras.layers.Dense(1024, activation='relu'),
    tf.keras.layers.Dense(1024, activation='relu'),
    tf.keras.layers.Dense(256, activation='relu'),
    tf.keras.layers.Dense(1, activation='sigmoid')
])


initial_learning_rate = 0.00005
decay_rate = 0.90

lr_scheduler = ExponentialDecay(
    initial_learning_rate, 
    decay_steps=10000, 
    decay_rate=decay_rate, 
    staircase=True
)


model.compile(optimizer=tf.keras.optimizers.Adam(learning_rate=lr_scheduler),
              loss='binary_crossentropy',
              metrics=['accuracy'])

# Train the model with validation split
history = model.fit(np.array(train_x), np.array(train_y), epochs=10)

# Save the trained model
model.save('usingmuselsl/epic_data.keras')