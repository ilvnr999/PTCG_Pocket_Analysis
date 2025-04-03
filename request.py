import requests
import base64

# API 的 URL
url = "http://127.0.0.1:8000/analyze"

# 上傳的檔案和表單數據
files = {'file': open('filtered_data.csv', 'rb')}  # 確保檔案路徑正確
data = {
    'time1': '2025-01-01,2025-01-02',  # 第一個時間範圍
    'time2': '2025-02-01,2025-02-02'   # 第二個時間範圍
}

# 發送 POST 請求
response = requests.post(url, files=files, data=data)

# 處理回應
if response.status_code == 200:
    result = response.json()
    print("Top Keywords:", result["top_keywords"])

    # 將 Base64 圖像解碼並保存為 PNG 文件
    image_base64 = result["image"]
    with open("output_image.png", "wb") as image_file:
        image_file.write(base64.b64decode(image_base64))
    print("圖片已保存為 output_image.png")
else:
    print("Error:", response.status_code, response.text)