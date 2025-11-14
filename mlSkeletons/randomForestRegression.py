import math
import numpy as np
import pandas as pd
import yfinance as yf
import matplotlib.pyplot as plt
from stockFunctions import stockData_years, stockData_preprocess, stockData_summary
from sklearn.model_selection import train_test_split, cross_val_score, TimeSeriesSplit, RandomizedSearchCV
from sklearn.preprocessing import MinMaxScaler
from sklearn.ensemble import RandomForestRegressor
from sklearn.metrics import mean_squared_error, r2_score

ticker = "RTX"    # REPLACE THIS WITH A PASSED INPUT STRING FOR THE TICKER INPUT 
years = 5        # best kept at 5 years of data

# 1. Load, summarize, and merge data
raw_data = stockData_years(years, ticker)
summary_df = stockData_summary(raw_data)
data = raw_data[['Open', 'High', 'Low', 'Close', 'Volume']].join(
    summary_df[['AveragePrice', 'WeightedAveragePrice', 'TrendBias']],
    how='inner'
)

# 2. Preprocessing & Target Creation (RETURNS)
data = stockData_preprocess(data)
data['TargetNextReturn'] = data['AveragePrice'].pct_change().shift(-1)
data = data.iloc[1:-1] # Drop the first row (NaN return) and the last row (NaN target)

print(f"Raw data rows: {len(raw_data)}")
print(f"Data rows ready for split: {len(data)}")

# we want the features to be RETURNS
features = ['Open', 'High', 'Low', 'Close', 'Volume', 'AveragePrice', 'WeightedAveragePrice']
X = data[features].pct_change()
X['TrendBias'] = data['TrendBias'] # Keep TrendBias as is
y = data['TargetNextReturn']

X = X.iloc[1:] # Drop the first row of X (NaNs from pct_change)
y = y.iloc[1:]

# 3. Train/Test Split
X_train, X_test, y_train, y_test = train_test_split(
    X, y, test_size=0.2, shuffle=False
)

# 4. Scale features
scaler = MinMaxScaler()
X_train_scaled = scaler.fit_transform(X_train)
X_test_scaled  = scaler.transform(X_test)

# 5. RandomizedSearchCV for hyperparameter optimization
param_grid = {
    'n_estimators': [50, 100, 150, 200],
    'max_depth': [5, 10, 15, None],
    'min_samples_split': [2, 5, 10],
    'min_samples_leaf': [1, 2, 4],
    'max_features': [0.5, 0.7, 1.0, 'sqrt']
}

tscv = TimeSeriesSplit(n_splits=5)

rf_random = RandomizedSearchCV(
    estimator=RandomForestRegressor(random_state=42, n_jobs=-1),
    param_distributions=param_grid,
    n_iter=20, # Number of settings sampled
    cv=tscv,
    verbose=0,
    random_state=42,
    scoring='r2',
    n_jobs=-1
)

rf_random.fit(X_train_scaled, y_train)
best_model = rf_random.best_estimator_

print("\n=== Hyperparameter Optimization Results ===")
print("Best parameters found: ", rf_random.best_params_)
print("Best cross-validation R² score: ", rf_random.best_score_)


# 6. Evaluation using the BEST Model
y_pred_return = best_model.predict(X_test_scaled)
mse = mean_squared_error(y_test, y_pred_return)
r2 = r2_score(y_test, y_pred_return)
rmse = math.sqrt(mse)

print("\n=== Best Model Performance Metrics (Predicting RETURNS) ===")
print(f"R² Score: {r2:.4f}")
print(f"MSE: {mse:.6f}")
print(f"RMSE: {rmse:.6f}")

# 7. Final Prediction & Visualization (Unscaling the return to price)
test_price_start_index = data.index.get_loc(X_test.index[0]) - 1
actual_prices = data['AveragePrice'].iloc[test_price_start_index:].copy()
actual_prices = actual_prices.iloc[1:]

predicted_prices = [actual_prices.iloc[0]]
for i in range(len(y_pred_return)):
    next_price = predicted_prices[-1] * (1 + y_pred_return[i])
    predicted_prices.append(next_price)
predicted_prices = predicted_prices[1:]

# plotting (COMMENTED OUT; THIS WAS USED FOR TESTING)
"""
plt.figure(figsize=(12,6))
plt.plot(actual_prices.index, actual_prices.values, label='Actual Price', color='blue')
plt.plot(actual_prices.index, predicted_prices, label='Predicted Price (Optimized RF)', color='orange')
plt.title(f"Optimized Random Forest Price Prediction (Trained on Returns)")
plt.xlabel("Date")
plt.ylabel("Average Price ($)")
plt.legend()
plt.savefig("random_forest_regression_optimized_returns_prediction.png")
"""

# final next-day price prediction
latest_X = X.iloc[-1].to_frame().T
latest_scaled = scaler.transform(latest_X)

predicted_next_return = best_model.predict(latest_scaled)[0]
last_actual_price = data['AveragePrice'].iloc[-1]
predicted_next_avg_price = last_actual_price * (1 + predicted_next_return)

print(f"\nLast known average price: ${last_actual_price:.2f}")
print(f"Predicted next day return: {predicted_next_return * 100:.4f}%")
print(f"Predicted next average price for {ticker}: ${predicted_next_avg_price:.2f}")
