import pandas as pd
from datetime import datetime 

def read_data(file_path, times):
    '''讀取資料，並轉換日期格式'''
    df = pd.read_csv(file_path, encoding='utf-8', parse_dates=["Date"])
    return df


def format_date(date_str):
    '''將輸入的日期轉換為固定格式 YYYY-MM-DD'''
    try:
        # 如果是連續的八個數字，轉換為 YYYY-MM-DD 格式
        if len(date_str) == 8 and date_str.isdigit():
            return datetime.strptime(date_str, "%Y%m%d").strftime("%Y-%m-%d")
        # 如果是標準的 YYYY-MM-DD 格式，直接處理
        return datetime.strptime(date_str.strip(), "%Y-%m-%d").strftime("%Y-%m-%d")
    except ValueError:
        raise ValueError(f"日期格式錯誤：{date_str}，請使用 YYYY-MM-DD 或 8 位數字格式")

def filter_data(df, times):
    '''過濾資料，並計算符合條件的評論數量和天數'''
    try:
        start_date, end_date = map(format_date, times.split(','))
    except ValueError as e:
        print(e)
        return
    mask = (df['Date'] >= start_date) & (df['Date'] <= end_date)
    start_date_obj = datetime.strptime(start_date, "%Y-%m-%d")
    end_date_obj = datetime.strptime(end_date, "%Y-%m-%d")
    days = (end_date_obj - start_date_obj).days
    return df.loc[mask], mask.sum(), days+1

def main(file_path, time1, time2):
    df = read_data(file_path, time1)
    
    out1,  num_of_comment1, days1= filter_data(df, time1)
    out2,  num_of_comment2, days2= filter_data(df, time2)
    out1.to_csv('filtered_data1.csv', index=False)
    out2.to_csv('filtered_data2.csv', index=False)
    print("第一個時間段",num_of_comment1, num_of_comment1/days1)

if __name__ == "__main__":
    file_path = 'PTCG_Pocket.csv'
    time1 = input('請輸入第一個時間範圍(YYYY-MM-DD,YYYY-MM-DD): ')
    time2 = input('請輸入第二個時間範圍(YYYY-MM-DD,YYYY-MM-DD): ')
    main(file_path, time1, time2)