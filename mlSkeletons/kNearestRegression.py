import math
import numpy as np
import pandas as pd
import yfinance as yf
import matplotlib.pyplot as plt
from stockFunctions import stockData_years, stockData_summary, stockData_preprocess
from sklearn.model_selection import train_test_split, cross_val_score, TimeSeriesSplit
from sklearn.neighbors import KNeighborsRegressor
from sklearn.metrics import mean_squared_error, r2_score
from sklearn.preprocessing import MinMaxScaler

ticker = "RTX"    # REPLACE THIS LATER WITH INPUT
years = 5    # 5 year time period

# 1. Load, summarize, and merge data
raw_data = stockData_years(years, ticker)
print(f"Raw data rows: {len(raw_data)}")

summary_df = stockData_summary(raw_data)
data = raw_data[['Open', 'High', 'Low', 'Close', 'Volume']].join(
    summary_df[['AveragePrice', 'WeightedAveragePrice', 'TrendBias']],
    how='inner'
)

# 2. Preprocessing & Target Creation (Simple NaN drop only)
data = stockData_preprocess(data)

# Create target: next day's average price
data['TargetNextAvg'] = data['AveragePrice'].shift(-1)
data = data.iloc[:-1]  # Drop last row with NaN target

print(f"Data rows ready for split: {len(data)}")

# 3. Features, Target, Train/Test Split
X = data[['Open','High','Low','Close','Volume','AveragePrice','WeightedAveragePrice','TrendBias']]
y = data['TargetNextAvg']

# Train/Test split (time-series safe)
X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, shuffle=False)

# 4. Scale features using unfiltered training data
scaler = MinMaxScaler()
X_train_scaled = scaler.fit_transform(X_train)
X_test_scaled  = scaler.transform(X_test)

# 5. Train & Prediction
model = KNeighborsRegressor(n_neighbors=10)
# Train using the full training data
model.fit(X_train_scaled, y_train)

y_pred = model.predict(X_test_scaled)    #prediction

# 6. Evaluation
mse = mean_squared_error(y_test, y_pred)
r2 = r2_score(y_test, y_pred)
rmse = math.sqrt(mse)

print("\n=== Performance Metrics ===")
print(f"R² Score: {r2:.4f}")
print(f"MSE: {mse:.4f}")
print(f"RMSE: {rmse:.4f}")

# timeSeries-safe cross-validation
tscv = TimeSeriesSplit(n_splits=5)
cv_scores = cross_val_score(model, X_train_scaled, y_train, cv=tscv, scoring='r2')

print(f"\nTimeSeries CV R² Scores: {cv_scores}")
print(f"Average CV R²: {cv_scores.mean():.4f}")

# 7. Plotting (COMMENTED OUT FOR FUTURE IMPLEMENTATION; PRIMARILY USED FOR TESTING)
"""
plt.figure(figsize=(12,6))
plt.plot(y_test.values, label='Actual', color='blue')
plt.plot(range(len(y_pred)), y_pred, label='Predicted', color='orange')
plt.title(f"KNN Regression - {ticker} ({years} Years of Data) - Final Corrected Model")
plt.xlabel("Sample Index")
plt.ylabel("Next Day Average Price ($)")
plt.legend()
plt.savefig("knn_regression_prediction_final.png")
"""

# 8. Predict next day average price
latest_point_df = pd.DataFrame(
    [X.iloc[-1]],
    columns=X.columns
)

latest_scaled = scaler.transform(latest_point_df)
predicted_next_avg = model.predict(latest_scaled)[0]

print(f"\nPredicted next average price for {ticker}: ${predicted_next_avg:.2f}")
