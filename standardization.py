import pandas as pd
import csv
'''csv檔案中看到content有些因為跳行或是“”的關係，影響行的值有的多出一行，所以透過file -I PTCG_Pocket.csv得知編碼\
    是utf-16le，然後用python的pandas讀取csv檔案，並且將encoding設為utf-16le，這樣就可以正確讀取csv檔案了'''
df = pd.read_csv('PTCG_Pocket.csv', encoding='utf-16le', sep='\t')
df.to_csv('filtered_data.csv', index=False, quotechar='"', quoting=csv.QUOTE_ALL)
print("CSV file has been standardized.")