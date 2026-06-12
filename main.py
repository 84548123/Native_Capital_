import os
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt

# Import specific functions rather than using *
# from forecast_model import train_forecast_model (COMMENTED OUT: Function does not exist)

# -----------------------------
# CREATE OUTPUT FOLDERS
# -----------------------------
os.makedirs("outputs/reports", exist_ok=True)
os.makedirs("outputs/charts", exist_ok=True)

# -----------------------------
# LOAD & PREP DATA
# -----------------------------
df = pd.read_csv("Native_Capital.csv")

df.rename(columns={
    'Nifty50 Index Value': 'Nifty50',
    'Nifty SmallCap 250 Index': 'Smallcap250'
}, inplace=True)

df['Date'] = pd.to_datetime(df['Date'], format='mixed') # Fixed Date Parsing Bug

df['Ratio'] = df['Nifty50'] / df['Smallcap250']
df['Nifty_Return'] = df['Nifty50'].pct_change()
df['Smallcap_Return'] = df['Smallcap250'].pct_change()

df['Nifty_Weight'] = 0.5
df['Smallcap_Weight'] = 0.5

df['Daily_Return'] = (df['Nifty_Weight'] * df['Nifty_Return']) + (df['Smallcap_Weight'] * df['Smallcap_Return'])
df['Portfolio_Value'] = (1 + df['Daily_Return']).cumprod() * 100000 

df['Nifty_Portfolio'] = (1 + df['Nifty_Return'].fillna(0)).cumprod() * 100000
df['Smallcap_Portfolio'] = (1 + df['Smallcap_Return'].fillna(0)).cumprod() * 100000
df['Static_50_50'] = (1 + (0.5 * df['Nifty_Return'].fillna(0) + 0.5 * df['Smallcap_Return'].fillna(0))).cumprod() * 100000

running_max = df['Portfolio_Value'].cummax()
df['Drawdown'] = (df['Portfolio_Value'] - running_max) / running_max

df.dropna(inplace=True)
df.to_csv("outputs/reports/backtest_results.csv", index=False)
print("Backtest results saved to outputs/reports/backtest_results.csv")