import pandas as pd
from datetime import datetime 

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


def filter_df(df, start_date, end_date):
    '''截取時間範圍內的資料'''
    mask = (df['Date'] >= start_date) & (df['Date'] <= end_date)
    start_date_obj = datetime.strptime(start_date, "%Y-%m-%d")
    end_date_obj = datetime.strptime(end_date, "%Y-%m-%d")
    days = (end_date_obj - start_date_obj).days
    return df.loc[mask], mask.sum(), days+1


def main():
    df = pd.read_csv('PTCG_Pocket.csv', encoding='utf-8', parse_dates=["Date"])
    times = input('請輸入時間範圍(YYYY-MM-DD,YYYY-MM-DD): ')
    try:
        start_date, end_date = map(format_date, times.split(','))
    except ValueError as e:
        print(e)
        return
    out,  num_of_comment, days= filter_df(df, start_date, end_date)
    out.to_csv('filtered_data.csv', index=False)
    print(num_of_comment, num_of_comment/days)



if __name__ == "__main__":
    main()