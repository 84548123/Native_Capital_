# generate_report.py
import os
import pandas as pd
import numpy as np

CSV_PATH = "Native_Capital.csv"
OUTPUT_EXCEL = "Nifty50_Technicals_Report.xlsx"

def generate_excel_report():
    print("Initializing Quantitative Excel Report Generator...")
    
    if not os.path.exists(CSV_PATH):
        print(f"Error: {CSV_PATH} not found. Please ensure the base CSV file is in this directory.")
        return

    # Load raw historical ledger
    df = pd.read_csv(CSV_PATH)
    df.columns = [c.strip() for c in df.columns]
    
    # Clean and sort dates chronologically (essential for rolling windows)
    df["Date"] = pd.to_datetime(df["Date"], errors="coerce")
    df.sort_values("Date", inplace=True)
    df.reset_index(drop=True, inplace=True)

    # Rename column if using the raw structural layout
    if "Nifty50 Index Value" in df.columns:
        df.rename(columns={"Nifty50 Index Value": "Nifty50"}, inplace=True)
    elif "Nifty50" not in df.columns:
        print("Error: Could not locate Nifty 50 pricing values in the CSV columns.")
        return

    # Create a dedicated report DataFrame focusing strictly on Nifty 50 metrics
    report_df = pd.DataFrame()
    report_df["Date"] = df["Date"].dt.strftime("%Y-%m-%d")
    report_df["Nifty50_Close"] = df["Nifty50"]

    print("Calculating rolling windows (1Week, 1Month, 1Year)...")
    # Standard market horizons: 1 Week = 5 trading sessions, 1 Month = 21 sessions, 1 Year = 252 sessions
    report_df["1W_Rolling_Return"] = df["Nifty50"].pct_change(periods=5)
    report_df["1M_Rolling_Return"] = df["Nifty50"].pct_change(periods=21)
    report_df["1Y_Rolling_Return"] = df["Nifty50"].pct_change(periods=252)

    print("Calculating Simple Moving Averages (50 SMA & 200 SMA)...")
    report_df["50_Day_SMA"] = df["Nifty50"].rolling(window=50).mean()
    report_df["200_Day_SMA"] = df["Nifty50"].rolling(window=200).mean()

    print("Calculating Exponential Moving Averages (50 EMA & 200 EMA)...")
    report_df["50_Day_EMA"] = df["Nifty50"].ewm(span=50, adjust=False).mean()
    report_df["200_Day_EMA"] = df["Nifty50"].ewm(span=200, adjust=False).mean()

    print("Calculating Relative Strength Index (14-Day RSI)...")
    delta = df["Nifty50"].diff()
    gain = delta.where(delta > 0, 0)
    loss = -delta.where(delta < 0, 0)

    # Smooth the average gains and losses using Wilder's exponential smoothing technique
    avg_gain = gain.ewm(com=13, adjust=False).mean()
    avg_loss = loss.ewm(com=13, adjust=False).mean()

    rs = avg_gain / avg_loss
    report_df["14_Day_RSI"] = np.where(avg_loss == 0, 100, 100 - (100 / (1 + rs)))

    # Clean up empty calculation padding rows resulting from high lookback boundaries gracefully
    report_df.fillna(0, inplace=True)

    # Flip order to descending (newest rows first) so the report opens showing current market data
    report_df = report_df.iloc[::-1]

    print(f"Exporting calculated vectors to Excel layout -> {OUTPUT_EXCEL}")
    
    # Save using the standard formatting engine
    with pd.ExcelWriter(OUTPUT_EXCEL, engine='openpyxl') as writer:
        report_df.to_excel(writer, index=False, sheet_name="Nifty50 Technicals")
        
        # Access openpyxl workbook internals to adjust visual column sizes automatically
        workbook = writer.book
        worksheet = workbook["Nifty50 Technicals"]
        for col in worksheet.columns:
            max_len = max(len(str(cell.value or '')) for cell in col)
            col_letter = chr(64 + col[0].column) if col[0].column <= 26 else "A" # Quick safe mapping ASCII letter rule
            worksheet.column_dimensions[col_letter].width = max(max_len + 3, 12)

    print("Excel technical matrix report generated successfully!")

if __name__ == "__main__":
    generate_excel_report()