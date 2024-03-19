import tensorflow as tf
import csv
import numpy as np
import sys

x_train = []
y_train = []

PREVIOUS = 25

previous_xs = []
previous_ys = []

def convert_labels(arr):
    if [0, 1] in arr:
        return [0, 1]
    return [1, 0]

with open("2024-03-15 14:37:35.241376") as f:
    reader = csv.reader(f)
    for row in reader:
        input = [
            float(row[1]),
            float(row[2]),
            float(row[3]),
            float(row[4])
        ]

        expected = [0, 1] if row[5] == "True" else [1, 0]  # Convert labels to one-hot encoded vectors

        previous_xs.append(input)
        previous_ys.append(expected)

        if len(previous_xs) > PREVIOUS:
            previous_xs.pop(0)
            previous_ys.pop(0)

            x_train.append(np.array(previous_xs).flatten())  # Flatten and append to x_train
            y_train.append(convert_labels(previous_ys)) # Append the last label to y_train

# Convert lists to numpy arrays
x_train = np.array(x_train)
y_train = np.array(y_train)

model = tf.keras.models.Sequential([
    tf.keras.layers.Input(shape=(PREVIOUS * 4,)),  # Input layer with the appropriate shape
    tf.keras.layers.Dense(128, activation='relu'),
    tf.keras.layers.Dropout(0.2),
    tf.keras.layers.Dense(2, activation='softmax')  # Output layer with 2 units for binary classification
])

loss_fn = tf.keras.losses.CategoricalCrossentropy()

model.compile(optimizer='adam',
              loss=loss_fn,
              metrics=['accuracy'])

model.fit(x_train, y_train, epochs=100)

model.save('data_test.keras')

loss, accuracy = model.evaluate(x_train, y_train, verbose=2)
print("Accuracy:", accuracy)
