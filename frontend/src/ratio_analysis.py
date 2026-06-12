def calculate_ratio(df):

    df['Ratio'] = df['Nifty50'] / df['Smallcap250']

    return df


def future_returns(df):

    # 252 trading days = 1 year

    df['Nifty_12M_Return'] = (
        df['Nifty50'].shift(-252) / df['Nifty50']
    ) - 1

    df['Smallcap_12M_Return'] = (
        df['Smallcap250'].shift(-252) / df['Smallcap250']
    ) - 1

    return df