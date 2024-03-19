import tensorflow as tf
import csv
import numpy as np
import sys
from training_constants import CHUNK_LENGTH, CHUNK_OVERLAP
from keras.optimizers.schedules import ExponentialDecay

x_train = []
y_train = []

xs = []
ys = []

def chunk_generator(arr, length, overlap):
    for i in range(0, len(arr), length - overlap):
        yield arr[i:i + length]

def convert_labels(arr):
    if [0, 1] in arr:
        return [0, 1]
    return [1, 0]

with open("2024-03-19 10:07:20.144829") as f:
    reader = csv.reader(f)
    for row in reader:
        input = [
            float(row[1]),
            float(row[2]),
            float(row[3]),
            float(row[4])
        ]

        expected = [0, 1] if row[5] == "True" else [1, 0]  # Convert labels to one-hot encoded vectors

        xs.append(input)
        ys.append(expected)

    f.close()

for x, y in zip(chunk_generator(xs, CHUNK_LENGTH, CHUNK_OVERLAP), chunk_generator(ys, CHUNK_LENGTH, CHUNK_OVERLAP)):
    flattened_x = np.array(x).flatten()  # Flatten the input chunk
    x_train.append(flattened_x)
    y_train.append(convert_labels(y))

print(len(x_train), len(y_train))

leng = 61275
x_train, y_train = np.array(x_train[:leng]), np.array(y_train[:leng])

model = tf.keras.models.Sequential([
    tf.keras.layers.Input(shape=(CHUNK_LENGTH * 4,)),
    tf.keras.layers.Dense(128, activation='relu'),
    tf.keras.layers.Dense(128, activation='relu'),
    tf.keras.layers.Dropout(0.1),
    tf.keras.layers.Dense(2, activation='softmax')  # Output layer with 2 units for binary classification
])

# Define initial learning rate and decay rate
initial_learning_rate = 0.001
decay_rate = 0.95

# Create a learning rate scheduler
lr_scheduler = ExponentialDecay(
    initial_learning_rate, 
    decay_steps=10000,  # Adjust the decay steps as needed
    decay_rate=decay_rate, 
    staircase=True
)

loss_fn = tf.keras.losses.CategoricalCrossentropy()

model.compile(optimizer=tf.keras.optimizers.Adam(learning_rate=lr_scheduler),
              loss='categorical_crossentropy',
              metrics=['accuracy'])

# Train your model
model.fit(x_train, y_train, epochs=100)

# Save the trained model
model.save('data_test.keras')

# Evaluate the model
loss, accuracy = model.evaluate(x_train, y_train, verbose=2)
print("Accuracy:", accuracy)
