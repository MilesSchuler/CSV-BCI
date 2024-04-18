from collections import defaultdict
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from sklearn.preprocessing import StandardScaler
from imblearn.over_sampling import RandomOverSampler
from sklearn.model_selection import train_test_split

from sklearn.neighbors import KNeighborsClassifier
from sklearn.metrics import classification_report
from collections import Counter

from scipy.stats import linregress

import random 

def most_frequent(List):
    occurence_count = Counter(List)
    return occurence_count.most_common(1)[0][0]

df = pd.read_csv('example_data.csv') 

value_counts = df['Direction'].value_counts()
num_to_remove = value_counts.iloc[0] - value_counts.iloc[1]

print(len(df))

dropped_rows = 0

while dropped_rows < num_to_remove:
    random_index = random.randrange(len(df))
    if df.iloc[random_index, 6] == 'none':
        df.drop(random_index) 
        dropped_rows+=1

print(len(df))



Y = df['Direction']
X = df.drop(columns = ['Direction', 'Timestamp', 'Sensor 5'])

# slopes = [] 
# directions = [] 

# wave_values = []

# # [[1, 2, 3, 4], [1, 2, 3, 4], [1, 2, 3, 4], [1, 2, 3, 4], [1, 2, 3, 4]]

# # [3, 6, 2, 1]

# x_range = [1, 2, 3, 4, 5]

# i = 0
# print(X)
# for wave_value in X: 
#     wave_values.append(wave_value)
#     if(i%5 == 0 and i > 0):
#         waves = X[i-5:i+1]
#         slopes_in_range = []
#         for row in range(0, 3):
#             sens_vals = []
#             for col in range(0, 4): 
#                 sens_vals.append(wave_values[row][col])
            
#             slope = linregress(x_range, sens_vals).slope
#             slopes_in_range.append(slope)
        
#         slopes.append(slopes_in_range)
#         directions_to_choose = Y[i-5:i+1]
#         direction = most_frequent(directions_to_choose)

#         directions.append(direction)

#         wave_values = [] 

#     i+=1



x_train, x_test, y_train, y_test = train_test_split(X, Y, test_size=0.2, random_state=0)

from sklearn.linear_model import LogisticRegression

lg_model = LogisticRegression()
lg_model = lg_model.fit(x_train, y_train)

y_pred = lg_model.predict(x_test)
print(classification_report(y_test, y_pred))
