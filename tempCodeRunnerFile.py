import requests
import time
import os
from datetime import datetime
import csv
import re

# Headers chung để gửi request
headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/114.0.0.0 Safari/537.36",
    "Accept": "application/json",
}

# Hàm trích xuất product_id từ URL sản phẩm
def extract_product_id(url, platform):
    if platform == "tiki":
        match = re.search(r"p(\d+)(?:.+spid=(\d+))?", url)
    elif platform == "sendo":
        match = re.search(r"-(\d+)\.html", url)
    else:
        return None, None

    product_id = match.group(1) if match else None
    spid = match.group(2) if match and len(match.groups()) > 1 else None
    return product_id, spid

# Hàm lấy review từ Tiki
def get_tiki_reviews(product_id, spid, output_file, limit=20):
    api_url = f"https://tiki.vn/api/v2/reviews?limit={limit}&page=1&spid={spid}&product_id={product_id}"
    response = requests.get(api_url, headers=headers)

    if response.status_code == 200:
        data = response.json()
        last_page = data.get("paging", {}).get("last_page", 1)
    else:
        print("Lỗi khi lấy tổng số trang từ Tiki!")
        return

    all_reviews = []
    for page in range(1, last_page + 1):
        api_url = f"https://tiki.vn/api/v2/reviews?limit={limit}&page={page}&spid={spid}&product_id={product_id}"
        response = requests.get(api_url, headers=headers)

        if response.status_code == 200:
            data = response.json()
            reviews = data.get("data", [])
            all_reviews.extend(reviews)
        time.sleep(1)

    save_reviews_to_csv(all_reviews, output_file)

# Hàm lấy review từ Sendo
def get_sendo_reviews(product_id, output_file, limit=10):
    api_url = f"https://ratingapi.sendo.vn/product/{product_id}/rating?page=1&limit={limit}&sort=review_score&v=2&star=all"
    response = requests.get(api_url, headers=headers)

    if response.status_code == 200:
        data = response.json()
        last_page = data.get("meta_data", {}).get("total_page", 1)
    else:
        print("Lỗi khi lấy tổng số trang từ Sendo!")
        return

    all_reviews = []
    for page in range(1, last_page + 1):
        api_url = f"https://ratingapi.sendo.vn/product/{product_id}/rating?page={page}&limit={limit}&sort=review_score&v=2&star=all"
        response = requests.get(api_url, headers=headers)

        if response.status_code == 200:
            data = response.json()
            reviews = data.get("data", [])
            all_reviews.extend(reviews)
        time.sleep(1)

    save_reviews_to_csv_sendo(all_reviews, output_file)

# Hàm lưu dữ liệu vào file CSV (Tiki)
def save_reviews_to_csv(reviews, filename):
    os.makedirs("result", exist_ok=True)
    filepath = os.path.join("result", filename)

    with open(filepath, mode="w", newline="", encoding="utf-8-sig") as file:
        writer = csv.writer(file)
        writer.writerow(["review_id", "rating", "content", "created_at"])
        for review in reviews:
            timestamp = review.get("created_at")
            formatted_date = datetime.utcfromtimestamp(timestamp).strftime("%Y-%m-%d %H:%M:%S") if timestamp else "N/A"
            writer.writerow([
                review.get("id"),
                review.get("rating"),
                review.get("content"),
                formatted_date,
            ])
    print(f"Dữ liệu đã lưu vào {filepath}")

# Hàm lưu dữ liệu vào file CSV (Sendo)
def save_reviews_to_csv_sendo(reviews, filename):
    os.makedirs("result", exist_ok=True)
    filepath = os.path.join("result", filename)

    with open(filepath, mode="w", newline="", encoding="utf-8-sig") as file:
        writer = csv.writer(file)
        writer.writerow(["review_id", "rating", "content", "comment_title", "user_name", "created_at"])
        for review in reviews:
            timestamp = review.get("update_time")
            formatted_date = datetime.utcfromtimestamp(timestamp).strftime("%Y-%m-%d %H:%M:%S") if timestamp else "N/A"
            writer.writerow([
                review.get("rating_id"),
                review.get("star"),
                review.get("comment"),
                review.get("comment_title"),
                review.get("user_name"),
                formatted_date,
            ])
    print(f"Dữ liệu đã lưu vào {filepath}")

# Chạy chương trình
if __name__ == "__main__":
    platform = input("Chọn nền tảng (1: Tiki, 2: Sendo): ").strip()
    url = input("Nhập link sản phẩm: ").strip()

    if platform == "1":
        platform_name = "tiki"
    elif platform == "2":
        platform_name = "sendo"
    else:
        print("Lựa chọn không hợp lệ!")
        exit()

    product_id, spid = extract_product_id(url, platform_name)
    if not product_id:
        print("Không tìm thấy product_id trong URL!")
    else:
        output_file = f"reviews_{product_id}.csv"
        if platform_name == "tiki":
            get_tiki_reviews(product_id, spid, output_file)
        elif platform_name == "sendo":
            get_sendo_reviews(product_id, output_file)
