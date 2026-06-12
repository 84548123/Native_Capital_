import pandas as pd

df = pd.read_csv("Native_Capital.csv")

print("Rows before:", len(df))

df["Date"] = pd.to_datetime(df["Date"], errors="coerce")

df = df[df["Date"].notna()]

df = df.sort_values("Date")

df.to_csv("Native_Capital.csv", index=False)

print("Rows after:", len(df))
print(df.tail(10))