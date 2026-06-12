import pandas as pd
import numpy as np

def calculate_market_regimes(df, window=21):
    """
    Classifies market regimes (e.g., Bull=1, Bear=0) based on rolling volatility and returns.
    """
    # Calculate rolling volatility and momentum
    df['Rolling_Vol'] = df['Daily_Return'].rolling(window=window).std()
    df['Momentum'] = df['Daily_Return'].rolling(window=window).mean()
    
    # Define Regime: 1 (Low Vol, Positive Momentum) -> Bull, 0 -> Bear/High Vol
    df['Regime'] = np.where(
        (df['Momentum'] > 0) & (df['Rolling_Vol'] < df['Rolling_Vol'].median()), 
        1, 0
    )
    
    # Calculate Transition Matrix (Probability of moving from State i to State j)
    df['Next_Regime'] = df['Regime'].shift(-1)
    
    # Build transition matrix
    transitions = pd.crosstab(df['Regime'], df['Next_Regime'], normalize='index')
    transitions.index = ['Bear', 'Bull']
    transitions.columns = ['Bear', 'Bull']
    
    return df, transitions

# Note: To integrate this cleanly with main.py without rewriting main.py's logic, 
# you would call calculate_market_regimes(df) right before the Monte Carlo step.