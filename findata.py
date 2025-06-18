import pandas as pd
from datetime import datetime, timedelta, date
import time
import yfinance as yf

from utils import finnhub_client, extract_concept

def get_history(symbol):

    tk = yf.Ticker(symbol)
    history = tk.history(period='2y', interval='1wk')
    history.index = history.index.date
    history = history[::-1]

    return history

def get_profits(q_report):

    symbol = q_report['symbol']
    data = []

    for quarter in q_report['data'][:9]:
        accepted_date = datetime.fromisoformat(quarter['acceptedDate'][:10]).date()
        profit = extract_concept(quarter, 'profit')
        data.append((accepted_date, profit))

    df = pd.DataFrame(data, columns=['date', symbol])
    df.set_index('date', inplace=True)
    return df


def add_profits_to_history(history_df, profits_df):

    result_df = history_df.copy()
    profits_column = profits_df.columns[0]

    result_df['profits'] = None

    # Convert profits index to list for easier searching
    profits_dates = sorted(profits_df.index.tolist())

    # For each date in history, find the most recent profits date
    for hist_date in result_df.index:
        # Find the most recent profits date that is <= hist_date
        valid_profits_dates = [p_date for p_date in profits_dates
                               if p_date <= hist_date]

        if valid_profits_dates:
            # Get the most recent valid profits date
            most_recent_profits_date = max(valid_profits_dates)
            # Set the profits value for this history date
            result_df.loc[hist_date, 'profits'] = (
                profits_df.loc[most_recent_profits_date, profits_column])

    return result_df

def aggregate_history_with_profits(symbol):

    ticker = yf.Ticker(symbol)
    try:
        num_shares = ticker.info['sharesOutstanding']
    except KeyError as e:
        print(f"Warning: Could not retrieve sharesOutstanding for {symbol}")
        print(ticker.info.keys())
        raise e
    history = get_history(symbol)
    q_reports = finnhub_client.financials_reported(symbol=symbol, freq='quarterly')
    profits = get_profits(q_reports)

    history = add_profits_to_history(history, profits)
    history['market_cap'] = history.Close * num_shares
    history['pe_ratio'] = history.market_cap / history.profits

    return history

def df_of_pe_ratios(*symbols):
    """
    Create a DataFrame with PE ratios for the given symbols.
    Each symbol will have its own column in the resulting DataFrame.
    """
    data = {}

    for symbol in symbols:
        history = aggregate_history_with_profits(symbol)
        data[symbol] = history['pe_ratio']

    df = pd.DataFrame(data)
    df.index.name = 'date'
    df.sort_index(inplace=True)

    return df

def main():
    df = df_of_pe_ratios('AAPL', 'MSFT', 'GOOGL', 'AMZN', 'TSLA',
                      'META', 'NFLX', 'NVDA')
    print(df)


if __name__ == '__main__':
    main()