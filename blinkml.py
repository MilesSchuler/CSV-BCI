# https://www.geeksforgeeks.org/sms-spam-detection-using-tensorflow-in-python/
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import tensorflow as tf
from tensorflow import keras
from keras import layers
from sklearn import model_selection
from sklearn.model_selection import train_test_split
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.naive_bayes import MultinomialNB
from sklearn.metrics import precision_score, recall_score, f1_score, classification_report,accuracy_score
import tensorflow_hub as hub
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler
from sklearn.svm import SVC
from sklearn.metrics import accuracy_score

# Load your EEG dataset
data = pd.read_csv('data.csv')

# Split the dataset into features (X) and labels (y)
X = data.drop('label', axis=1)
Y = data['label']

# Split the dataset into training and testing sets
X_train, X_test, Y_train, Y_test = train_test_split(X, Y, test_size=0.2, random_state=42)

# Standardize features by removing the mean and scaling to unit variance
scaler = StandardScaler()
X_train_scaled = scaler.fit_transform(X_train)
X_test_scaled = scaler.transform(X_test)

# Initialize and train a Support Vector Machine classifier
svm_classifier = SVC(kernel='linear', random_state=1)
svm_classifier.fit(X_train_scaled, Y_train)

# Predict the labels for the test set
Y_pred = svm_classifier.predict(X_test_scaled)

# Calculate the accuracy of the classifier
accuracy = accuracy_score(Y_test, Y_pred)
print("Accuracy:", accuracy)

def predict_label(TP9_value, AF7_value, AF8_value, TP10_value):
    mydict = {'TP9':TP9_value, 'AF7':AF7_value, 'AF8':AF8_value, 'TP10':TP10_value}
    temp = pd.DataFrame([mydict])
    data_array = np.array(temp).reshape(1, -1)
    # Standardize the input features
    input_scaled = scaler.transform(data_array)

    # Make predictions
    predicted_label = svm_classifier.predict(input_scaled)

    return predicted_label[0]

a = input("a")
b = input("b")
c = input("c")
d = input("d")

# focused,-1000.000,-510.742,-801.758,-138.184

print(predict_label(a,b,c,d))