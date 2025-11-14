import yfinance as yf
import pandas as pd


# input is the number of days & stock symbol
def stockData_days(days: int, ticker: str) -> pd.DataFrame:
    stock = yf.Ticker(ticker)
    data = stock.history(period= str(days) + "d") # specify day period with parameter

    # Ensure it's sorted by date (ascending)
    data = data.sort_index()

    # returns pd.DataFrame containing features: Open, High, Low, Close, Adj Close, and Volume.
    return data

# input is the number of months & stock symbol
def stockData_months(months: int, ticker: str) -> pd.DataFrame:
    stock = yf.Ticker(ticker)
    data = stock.history(period= str(years) + "mo") # specify month period with parameter

    # Ensure it's sorted by date (ascending)
    data = data.sort_index()

    # returns pd.DataFrame containing features: Open, High, Low, Close, Adj Close, and Volume.
    return data

# input is the number of years & stock symbol
def stockData_years(years: int, ticker: str) -> pd.DataFrame:
    stock = yf.Ticker(ticker)
    data = stock.history(period= str(years) + "y") # specify year period with parameter

    # Ensure it's sorted by date (ascending)
    data = data.sort_index()

    # returns pd.DataFrame containing features: Open, High, Low, Close, Adj Close, and Volume.
    return data

# input is just the stock symbol
# USE THIS IF THERE'S LESS THAN THE APPROPRIATE AMOUNT OF SAMPLES IN THE STOCK
def stockData_all(ticker: str) -> pd.DataFrame:
    stock = yf.Ticker(ticker)
    data = stock.history(period= "max") # ALL the available stock data for the 

    # Ensure it's sorted by date (ascending)
    data = data.sort_index()

    # returns pd.DataFrame containing features: Open, High, Low, Close, Adj Close, and Volume.
    return data


# input is the dataframe
# USE THIS FOR DISPLAY
def stockData_summary(df: pd.DataFrame) -> pd.DataFrame:
    summaries = []

    for date, row in df.iterrows():
        OPEN = row['Open']
        HIGH = row['High']
        LOW = row['Low']
        CLOSE = row['Close']

        avg_price = (OPEN + HIGH + LOW + CLOSE) / 4
        weighted_avg_price = (OPEN + HIGH + LOW + 2 * CLOSE) / 5
        trend_bias = (CLOSE - OPEN) / (HIGH - LOW) if (HIGH - LOW) != 0 else 0

        # numeric values only — no f-strings
        summaries.append({
            "AveragePrice": avg_price,
            "WeightedAveragePrice": weighted_avg_price,
            "TrendBias": trend_bias
        })

    summary_df = pd.DataFrame(summaries, index=df.index)
    summary_df.index.name = "Date"
    return summary_df

"""
#EXAMPLE USAGE
if __name__ == "__main__":
    ticker = "RTX"
    df = stockData_days(7, ticker)
    summary = stockData_summary(df)
    print(df)
    print(summary)
"""
