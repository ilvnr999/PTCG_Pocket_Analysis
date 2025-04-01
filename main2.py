import pandas as pd
import torch
from transformers import pipeline
import matplotlib.pyplot as plt
import seaborn as sns

# 讀取 CSV 文件
def load_data(file_path):
    df = pd.read_csv(file_path)
    df['date'] = pd.to_datetime(df['date'])  # 確保日期格式正確
    return df

# 過濾指定日期區間的評論
def filter_reviews(df, start_date, end_date):
    return df[(df['date'] >= start_date) & (df['date'] <= end_date)]

# 進行情感分析
sentiment_pipeline = pipeline("sentiment-analysis", model="cardiffnlp/twitter-roberta-base-sentiment")

def analyze_sentiment(reviews):
    results = sentiment_pipeline(reviews.tolist())
    return [res['label'] for res in results]

# 計算情感比例
def get_sentiment_distribution(labels):
    return pd.Series(labels).value_counts(normalize=True) * 100

# 視覺化結果
def plot_sentiment_comparison(dist1, dist2, period1, period2):
    df = pd.DataFrame({period1: dist1, period2: dist2}).fillna(0)
    df.plot(kind='bar', figsize=(8, 5), colormap='coolwarm')
    plt.title("Sentiment Comparison")
    plt.ylabel("Percentage")
    plt.show()

# 主函式
def main(file_path, period1, period2):
    df = load_data(file_path)
    df1 = filter_reviews(df, period1[0], period1[1])
    df2 = filter_reviews(df, period2[0], period2[1])
    
    df1['sentiment'] = analyze_sentiment(df1['review'])
    df2['sentiment'] = analyze_sentiment(df2['review'])
    
    dist1 = get_sentiment_distribution(df1['sentiment'])
    dist2 = get_sentiment_distribution(df2['sentiment'])
    
    plot_sentiment_comparison(dist1, dist2, str(period1), str(period2))
    
    print("Period 1 Sentiment Distribution:\n", dist1)
    print("Period 2 Sentiment Distribution:\n", dist2)

# 執行腳本
if __name__ == "__main__":
    file_path = "PTCG_Pocket.csv"  # 修改為你的文件路徑
    period1 = ("2024-01-01", "2024-02-01")
    period2 = ("2024-02-02", "2024-03-01")
    main(file_path, period1, period2)
