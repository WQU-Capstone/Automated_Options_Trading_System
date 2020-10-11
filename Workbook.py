# Importing libraries
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
%matplotlib inline
import statistics as stats
import math
from scipy.stats import norm
import datetime

# Setup Call & Put functions
def d_1(sigma, T, S, K, r):
    return 1/(sigma*np.sqrt(T))*(np.log(S/K)+(r+(sigma**2)/2)*T)

def d_2(d_1, sigma, T):
    return d_1 - sigma*np.sqrt(T)

def Call(sigma, T, S, K, r):
    d1 = d_1(sigma, T, S, K, r)
    d2 = d_2(d1, sigma, T)
    return norm.cdf(d1)*S-norm.cdf(d2)*K*np.exp(-r*T)

def Put(sigma, T, S, K, r):
    d1 = d_1(sigma, T, S, K, r)
    d2 = d_2(d1, sigma, T)
    return norm.cdf(-d2)*K*np.exp(-r*T)-norm.cdf(-d1)*S

# Load SPY ETF data
spy_df = pd.read_csv("SPY.csv")
pd.to_datetime(spy_df["Date"])
spy_df = spy_df[["Date","Adj Close"]]
spy_df = spy_df.set_index(pd.DatetimeIndex(spy_df["Date"]))
spy_df.drop("Date", axis = 1, inplace = True)

# Load VIX data
vix_df = pd.read_csv("VIX.csv")
pd.to_datetime(vix_df["Date"])
vix_df = vix_df[["Date","Adj Close"]]
vix_df = vix_df.set_index(pd.DatetimeIndex(vix_df["Date"]))
vix_df.drop("Date", axis = 1, inplace = True)

# Adding Bollinger Bands as technical indicator for portfolio rebalancing

spy_df['20 day moving average'] = spy_df['Adj Close'].rolling(window=20).mean()

spy_df['20 day std'] = spy_df['Adj Close'].rolling(window=20).std()

spy_df['Upper Band'] = spy_df['20 day moving average'] + (spy_df['20 day std'] * 1.5)
spy_df['Lower Band'] = spy_df['20 day moving average'] - (spy_df['20 day std'] * 1.5)


def option_payout(direction, opt_type, S, K):
    """
    Calculates an option pay out depending on direction (long/short),
    option type (call/put), current underlying level (S) and the option's strike (K)
    """
    if direction == "s":
        if opt_type == "p":
            return -max(0, K-S)
        else:
            return -max(0, S-K)
    else:
        if opt_type == "p":
            return max(0, K-S)
        else:
            return max(0, S-K)


# Initiating variables

# Initial investment state = 0 (not invested)
inv_state = 0

# Setting initial portfolio value to 0
pf_value = 0

# Creating list to keep track of portfolio values
pf_value_list = []

# Create portfolio dataframe with underlyings date index
pf_df = pd.DataFrame(index=spy_df.index)

# Looping through the data and short put options

for day in range(len(spy_df)):
    # Keeping track of every day's portfolio value
    pf_value_list.append(pf_value)
    cur_close = spy_df["Adj Close"].iloc[day]

    if cur_close > spy_df["Upper Band"].iloc[day] and inv_state == 0:
        # Creating a one month at-the-money option with that day volatilty (using VIX close as Proxy)
        p_strike = cur_close
        p_opt = Put(vix_df["Adj Close"].iloc[day] / 100, 1 / 12, cur_close, cur_close, 0.005)
        p_opt_exp = spy_df.index[day] + datetime.timedelta(days=30)

        # Set invested state to 1 = invested
        inv_state = 1

        # Adding option premium to portfolio value
        pf_value += p_opt

        print("option invested on", spy_df.index[day], "premium:", p_opt)

    if inv_state == 1 and spy_df.index[day] > p_opt_exp:
        # Calculating option premium at expiry
        opt_return = option_payout("s", "p", spy_df["Adj Close"].iloc[day], p_strike)
        print("Option expires", spy_df.index[day], "return:", opt_return)

        # Adding expiry value to portfolio value
        pf_value += opt_return

        # Setting investment state to "not invested" = 0
        inv_state = 0
print("pf end value:", pf_value)

# Adding each day's portfolio value to the portfolio dataframe
pf_df["Value"] = pf_value_list