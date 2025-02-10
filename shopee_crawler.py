import requests

url = "https://shopee.vn/api/v2/item/get_ratings"
params = {
    "itemid": 26319445803,  # ID sản phẩm
    "shopid": 33435563,      # ID shop
    "limit": 10,             # Số review muốn lấy
    "offset": 0,             # Offset để phân trang
    "type": 0,               # Loại review (0: tất cả)
    "filter": 0,             # Bộ lọc đánh giá
}

headers = {
    "User-Agent": "Mozilla/5.0",
    "Cookie": "SPC_F=xpRJH1SGNYtbIrIgihrmmFrqGBdRFYdv; REC_T_ID=668394ce-9e92-11ef-b28b-42d5ddb60d1a; _QPWSDCXHZQA=d9808e0f-b772-4d6d-eea7-894a57b15b84; ..."  # Copy toàn bộ cookie vào đây
}

response = requests.get(url, params=params, headers=headers)

if response.status_code == 200:
    data = response.json()
    print(data)  # Kiểm tra dữ liệu review
else:
    print("Lỗi:", response.status_code, response.text)
