import pandas as pd
import csv

df = pd.read_csv('PTCG_Pocket.csv', encoding='utf-16le', sep='\t')
df.to_csv('PTCG_Pocket.csv', index=False, quotechar='"', quoting=csv.QUOTE_ALL)
print("CSV file has been standardized.")