import math
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from sklearn.model_selection import train_test_split, cross_val_score
from sklearn.linear_model import LinearRegression
from sklearn.metrics import mean_squared_error, r2_score

# 1. Import Data
# TODO: Import data from YahooFinance and convert it into a dataframe

# 2. Data Preprocessing and Splitting

X = data[['Feature_X']] # X = historic price points
y = data['Target_y']    # y = target price OR trend

# Splitting: 80% training, 20% testing
X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)

# 3. Model Training

model = LinearRegression()
model.fit(X_train, y_train)

y_pred = model.predict(X_test)

# 4. Model Evaluation
mse = mean_squared_error(y_test, y_pred)
r2 = r2_score(y_test, y_pred)
rmse = math.sqrt(mse)

print("Performance Metrics")
print(f"R-squared (R2 Score): {r2:.4f}")
print(f"Mean Squared Error (MSE): {mse:.2f}")
print(f"Root Mean Squared Error (RMSE): {rmse:.2f}")
# TODO: Implement K-Fold CV score here


# 5. Visualizing (Graphs)
# TODO