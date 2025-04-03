import pandas as pd
from datetime import datetime 
from transformers import pipeline, AutoTokenizer
from yake import KeywordExtractor
from collections import Counter
import matplotlib.pyplot as plt

def read_data(file_path):
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
    if mask.sum() == 0:
        print("沒有符合條件的評論")
        return 0
    return df.loc[mask], mask.sum(), days+1

sentiment_pipeline = pipeline("sentiment-analysis", model="cardiffnlp/twitter-roberta-base-sentiment")
tokenizer = AutoTokenizer.from_pretrained("cardiffnlp/twitter-roberta-base-sentiment")

def extract_keywords_yake(comments, top_n=100):
    '''使用 YAKE 提取關鍵字'''
    extractor = KeywordExtractor(lan="en", n=3, dedupLim=0.9, top=top_n)
    all_keywords = []
    for comment in comments:
        keywords = extractor.extract_keywords(comment.lower())
        all_keywords.extend([kw[0] for kw in keywords])  # 提取關鍵字
    return Counter(all_keywords)  # 返回關鍵字的頻率

def compare_keyword_frequencies(freq1, freq2):
    '''比較兩個時段的關鍵字頻率變化'''
    all_keywords = set(freq1.keys()).union(set(freq2.keys()))
    comparison = []
    for keyword in all_keywords:
        freq_period1 = freq1.get(keyword, 0)
        freq_period2 = freq2.get(keyword, 0)
        change = freq_period2 - freq_period1
        comparison.append((keyword, change))
    # 按變化量排序
    comparison.sort(key=lambda x: x[1], reverse=True)
    return comparison

def analyze_sentiment(data):
    '''進行情感分析'''
    data.loc[:, 'Combined'] = data['Title'].fillna('') + data['Content'].fillna('')
    truncated_texts = [
        tokenizer.decode(tokenizer(text, max_length=512, truncation=True)['input_ids'])
        for text in data['Combined']
    ]
    results = sentiment_pipeline(truncated_texts)
    mapping = {
        'LABEL_0': 'Negative',
        'LABEL_1': 'Neutral',
        'LABEL_2': 'Positive'
    }
    return [mapping[res['label']] for res in results]


def trends(data, num_of_comment):
    sentiments = analyze_sentiment(data)
    sentiment_counts = {
        "positive": sentiments.count("Positive"),
        "negative": sentiments.count("Negative"),
        "neutral": sentiments.count("Neutral")  # RoBERTa 的標籤直接有 "neutral"
    }
    return {
        "total_reviews": num_of_comment,
        "sentiment_counts": sentiment_counts,
    }

def visualize_combined(trends1, trends2, num_of_comment1, days1, num_of_comment2, days2, period1, period2):
    '''將評論數量、情感分佈和成長趨勢合併到一個畫布中'''
    # 計算平均每天的評論數
    avg_comments1 = num_of_comment1 / days1
    avg_comments2 = num_of_comment2 / days2

    # 計算成長量
    avg_daily_negative1 = trends1['sentiment_counts']['negative'] / days1
    avg_daily_negative2 = trends2['sentiment_counts']['negative'] / days2
    total_growth = avg_comments2 - avg_comments1
    negative_growth = avg_daily_negative2 - avg_daily_negative1

    # 創建子圖
    fig, axes = plt.subplots(1, 3, figsize=(10, 14) , dpi=100) 
    fig.suptitle('Comment Analysis and Trends', fontsize=16)
    fig.subplots_adjust(hspace=0.4, wspace=0.4)

    # 子圖 1: 評論數量及平均每天的評論數（長條圖）
    df_comments = pd.DataFrame({
        'Metric': ['Total Comments', 'Average Daily Comments'],
        period1: [num_of_comment1, avg_comments1],
        period2: [num_of_comment2, avg_comments2]
    })
    df_comments.set_index('Metric', inplace=True)
    df_comments.plot(kind='bar', ax=axes[0], colormap='viridis')
    axes[0].set_title('Comment Trends Between Two Periods')
    axes[0].set_xlabel('Metric')
    axes[0].set_ylabel('Number of Comments')
    axes[0].legend(title='Period')
    axes[0].grid(axis='y')

    # 子圖 2: 情感分佈比較（長條圖）
    df_sentiments = pd.DataFrame({
        'Sentiment': ['Positive', 'Negative', 'Neutral'],
        period1: [trends1['sentiment_counts']['positive'], trends1['sentiment_counts']['negative'], trends1['sentiment_counts']['neutral']],
        period2: [trends2['sentiment_counts']['positive'], trends2['sentiment_counts']['negative'], trends2['sentiment_counts']['neutral']]
    })
    df_sentiments.set_index('Sentiment', inplace=True)
    df_sentiments.plot(kind='bar', ax=axes[1], colormap='coolwarm')
    axes[1].set_title('Sentiment Comparison Between Two Periods')
    axes[1].set_ylabel('Number of Comments')
    axes[1].set_xlabel('Sentiment')
    axes[1].grid(axis='y')

    # 子圖 3: 成長量比較（長條圖）
    growth_data = {
        'Metric': ['Total Growth', 'Negative Growth'],
        'Growth': [total_growth, negative_growth]
    }
    df_growth = pd.DataFrame(growth_data)
    axes[2].bar(df_growth['Metric'], df_growth['Growth'], color=['orange', 'red'])
    axes[2].set_title('Growth in Comments and Negative Comments')
    axes[2].set_ylabel('Growth per Day')
    axes[2].grid(axis='y')

    # 調整子圖間距
    plt.tight_layout()
    plt.show()



def main(file_path, time1, time2):
    df = read_data(file_path)
    
    df1,  num_of_comment1, days1= filter_data(df, time1)
    df2,  num_of_comment2, days2= filter_data(df, time2)

    df1['Sentiment'] = analyze_sentiment(df1)
    df2['Sentiment'] = analyze_sentiment(df2)

    df1.to_csv('filtered_data1.csv', index=False)
    df2.to_csv('filtered_data2.csv', index=False)

    keywords_freq1 = extract_keywords_yake(df1['Combined'].tolist(), top_n=20)
    keywords_freq2 = extract_keywords_yake(df2['Combined'].tolist(), top_n=20)

    # 比較關鍵字頻率變化
    keyword_comparison = compare_keyword_frequencies(keywords_freq1, keywords_freq2)

    # 輸出結果
    print("關鍵字頻率變化：")
    print(f"{'Keyword':<20}{'Change':<10}")
    for keyword, change in keyword_comparison[:5]:  # 顯示前 10 個變化最大的關鍵字
        print(f"{keyword:<20}{change:<10}")

    trends1 = trends(df1, num_of_comment1)
    trends2 = trends(df2, num_of_comment2)

    visualize_combined(trends1, trends2, num_of_comment1, days1, num_of_comment2, days2, time1, time2)

    #print("第一個時間段",trends1, num_of_comment1/days1)
    #print("第二個時間段",trends2, num_of_comment2/days2)

if __name__ == "__main__":
    file_path = 'PTCG_Pocket.csv'
    time1 = input('請輸入第一個時間範圍(YYYY-MM-DD,YYYY-MM-DD): ')
    time2 = input('請輸入第二個時間範圍(YYYY-MM-DD,YYYY-MM-DD): ')
    main(file_path, time1, time2)