import pandas as pd
import csv

def filter_df(df, start_date, end_date):
    mask = (df['Date'] >= start_date) & (df['Date'] <= end_date)
    return df.loc[mask]

def main():
    df = pd.read_csv('PTCG_Pocket.csv', encoding='utf-16le',sep='\t', parse_dates=["Date"])
    out = filter_df(df, '2025-03-24', '2025-03-25')
    out.to_csv('filtered_data.csv', index=False, quotechar='"', quoting=csv.QUOTE_ALL)

if __name__ == "__main__":
    main()