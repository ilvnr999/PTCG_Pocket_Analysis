from fastapi import FastAPI, File, Form, UploadFile, HTTPException
from fastapi.responses import JSONResponse
import pandas as pd
from datetime import datetime
from transformers import pipeline, AutoTokenizer
from yake import KeywordExtractor
from collections import Counter
import matplotlib.pyplot as plt
import io
import base64

# 建立api實例
app = FastAPI()

# 初始化情感分析模型
sentiment_pipeline = pipeline("sentiment-analysis", model="cardiffnlp/twitter-roberta-base-sentiment")
# 初始化分詞器
tokenizer = AutoTokenizer.from_pretrained("cardiffnlp/twitter-roberta-base-sentiment")


def read_data(file: UploadFile):
    try:
        df = pd.read_csv(file.file, encoding='utf-8', parse_dates=["Date"]) # utf-8編碼默認的寫法
        return df
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"檔案讀取失敗：{str(e)}")  # 防止服務器中斷，出錯時也比較清楚錯誤處在哪裡


def format_date(date_str):
    try:
        if len(date_str) == 8 and date_str.isdigit():   # 判斷輸入寫法是不是8位數字yyyyMMdd
            return datetime.strptime(date_str, "%Y%m%d").strftime("%Y-%m-%d")
        else:
            # 判斷輸入寫法是不是yyyy-MM-dd
            if len(date_str) == 10 and date_str[4] == '-' and date_str[7] == '-':
                return datetime.strptime(date_str.strip(), "%Y-%m-%d").strftime("%Y-%m-%d")
            else:
                # 判斷輸入寫法是不是yyyy/MM/dd
                if len(date_str) == 10 and date_str[4] == '/' and date_str[7] == '/':
                    return datetime.strptime(date_str.strip(), "%Y/%m/%d").strftime("%Y-%m-%d")
        return datetime.strptime(date_str.strip(), "%Y-%m-%d").strftime("%Y-%m-%d")
    except ValueError:
        raise HTTPException(status_code=400, detail=f"日期格式錯誤：{date_str}，請使用 YYYY-MM-DD 或 8 位數字格式")


def filter_data(df, times):
    try:
        start_date, end_date = map(format_date, times.split(',')) # 這裡的times是用逗號分隔的兩個時間範圍
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    mask = (df['Date'] >= start_date) & (df['Date'] <= end_date)    # 透過pandas series的布林值來篩選資料
    start_date_obj = datetime.strptime(start_date, "%Y-%m-%d")
    end_date_obj = datetime.strptime(end_date, "%Y-%m-%d")
    days = (end_date_obj - start_date_obj).days
    if mask.sum() == 0:
        raise HTTPException(status_code=400, detail="時間範圍內沒有符合條件的評論")
    return df.loc[mask].copy(), mask.sum(), days + 1


def extract_keywords_yake(comments, top_n=10):
    extractor = KeywordExtractor(lan="en", n=3, dedupLim=0.9, top=top_n)
    all_keywords = []
    for comment in comments:
        keywords = extractor.extract_keywords(comment.lower()) # [('sample', 0.1), ('comment', 0.2), ('this', 0.3)]
        all_keywords.extend([kw[0] for kw in keywords]) # 提取關鍵字
    return Counter(all_keywords) # 計算關鍵字的頻率回傳字典


def compare_keyword_frequencies(freq1, freq2):
    all_keywords = set(freq1.keys()).union(set(freq2.keys())) # 取得兩個字典的key的聯集
    comparison = []
    for keyword in all_keywords:
        freq_period1 = freq1.get(keyword, 0) # 取得該字詞的出現頻率沒有則為0
        freq_period2 = freq2.get(keyword, 0)
        change = freq_period2 - freq_period1
        comparison.append((keyword, change)) # 將字詞和變化量加入列表
    comparison.sort(key=lambda x: x[1], reverse=True) # 依照key排序 差異數大到小
    return comparison


def analyze_sentiment(data):
    data['Combined'] = data['Title'].fillna('') + data['Content'].fillna('')
    truncated_texts = [
        tokenizer.decode(tokenizer(text, max_length=512, truncation=True)['input_ids']) # 先透過tokenizer辨識哪個為重要的文字 透過decoder還原回文字縮減到512個token
        for text in data['Combined']
    ]
    results = sentiment_pipeline(truncated_texts)
    mapping = {
        'LABEL_0': 'Negative',
        'LABEL_1': 'Neutral',
        'LABEL_2': 'Positive'
    }
    return [mapping[res['label']] for res in results] # 將LABEL_0、LABEL_1、LABEL_2轉換為Negative、Neutral、Positive

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
    fig, axes = plt.subplots(1, 3, figsize=(15, 7) , dpi=100) 
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
    axes[0].set_ylabel('Number of Comments')
    axes[0].legend(title='Period')
    axes[0].grid(axis='y')
    axes[0].set_xlabel("")  # 移除 x 軸標籤
    axes[0].tick_params(axis='x', labelrotation=0)  # 將 x 軸文字改為水平

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
    axes[1].grid(axis='y')
    axes[1].set_xlabel("")  # 移除 x 軸標籤
    axes[1].tick_params(axis='x', labelrotation=0)  # 將 x 軸文字改為水平

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
    buf = io.BytesIO() # 創建一個BytesIO對象
    fig.savefig(buf, format='png') # 將圖像保存到BytesIO對象中
    buf.seek(0) 
    base64_image = base64.b64encode(buf.read()).decode('utf-8') # 將圖像轉換為Base64編碼
    buf.close()
    return base64_image


@app.post("/analyze") # 定義API的路由
async def analyze(  # 定義API的請求參數
    file: UploadFile = File(...), # 取得上傳的檔案
    time1: str = Form(...), # 取得第一個時間範圍
    time2: str = Form(...) # 取得第二個時間範圍
):
    # 讀取檔案
    df = read_data(file)

    # 過濾資料
    df1, num_of_comment1, days1 = filter_data(df, time1)
    df2, num_of_comment2, days2 = filter_data(df, time2)

    # 情感分析
    df1['Sentiment'] = analyze_sentiment(df1)
    df2['Sentiment'] = analyze_sentiment(df2)

    # 提取關鍵字
    keywords_freq1 = extract_keywords_yake(df1['Combined'].tolist(), top_n=20)
    keywords_freq2 = extract_keywords_yake(df2['Combined'].tolist(), top_n=20)

    # 比較關鍵字頻率
    keyword_comparison = compare_keyword_frequencies(keywords_freq1, keywords_freq2)

    trends1 = trends(df1, num_of_comment1)
    trends2 = trends(df2, num_of_comment2)

    image_base64 = visualize_combined(trends1, trends2, num_of_comment1, days1, num_of_comment2, days2, time1, time2)


        # 返回結果
    return JSONResponse(content={
        "top_keywords": [(keyword, int(change)) for keyword, change in keyword_comparison[:5]],  # 確保轉換為 Python int
        "num_of_comment1": int(num_of_comment1),  # 轉換為 Python int
        "num_of_comment2": int(num_of_comment2),  # 轉換為 Python int
        "image": image_base64
    })