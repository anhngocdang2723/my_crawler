import requests
import time
from datetime import datetime
import csv
import re

# Headers chung để gửi request
headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/114.0.0.0 Safari/537.36",
    "Accept": "application/json",
    "Referer": "https://tiki.vn/",
}

# Hàm trích xuất product_id và spid từ URL sản phẩm
def extract_tiki_ids(url):
    match = re.search(r"p(\d+)(?:.+spid=(\d+))?", url)
    product_id = match.group(1) if match else None
    spid = match.group(2) if match and match.group(2) else None
    return product_id, spid

# Hàm lấy tên sản phẩm
def get_product_name(product_id):
    api_url = f"https://tiki.vn/api/v2/products/{product_id}?platform=web&version=3"
    response = requests.get(api_url, headers=headers)
    if response.status_code == 200:
        data = response.json()
        return data.get("name", "Unknown Product")
    return "Unknown Product"

# Hàm lấy `spid` nếu không có trong URL
def get_spid_if_missing(product_id):
    api_url = f"https://tiki.vn/api/v2/reviews?limit=1&page=1&product_id={product_id}"
    response = requests.get(api_url, headers=headers)

    if response.status_code == 200:
        data = response.json()
        first_review = data.get("data", [{}])[0]
        return first_review.get("spid")
    return None

# Hàm lấy seller_id từ API reviews
def get_seller_id(product_id, spid):
    api_url = f"https://tiki.vn/api/v2/reviews?limit=1&page=1&spid={spid}&product_id={product_id}"
    response = requests.get(api_url, headers=headers)
    if response.status_code == 200:
        data = response.json()
        seller_id = data.get("data", [{}])[0].get("seller_id", 1)
        return seller_id
    return 1  # Mặc định là 1 nếu không lấy được

# Hàm lấy tổng số trang reviews
def get_total_pages(product_id, spid, seller_id, limit=20):
    api_url = f"https://tiki.vn/api/v2/reviews?limit={limit}&page=1&spid={spid}&product_id={product_id}&seller_id={seller_id}"
    response = requests.get(api_url, headers=headers)
    if response.status_code == 200:
        data = response.json()
        total_reviews = data.get("paging", {}).get("total", 0)
        last_page = data.get("paging", {}).get("last_page", 1)
        if total_reviews == 0:
            print("Sản phẩm này không có đánh giá nào!")
            return 0
        print(f"Tổng số đánh giá: {total_reviews}, Số trang cần lấy: {last_page}")
        return last_page
    else:
        print(f"Lỗi khi lấy tổng số trang: {response.status_code}")
        return 0

# Hàm crawl review từ trang 1 đến last_page
def crawl_reviews(product_id, spid, seller_id, output_file, limit=20):
    last_page = get_total_pages(product_id, spid, seller_id, limit)
    if last_page == 0:
        print("Không có đánh giá để lưu!")
        return

    all_reviews = []
    for page in range(1, last_page + 1):
        api_url = f"https://tiki.vn/api/v2/reviews?limit={limit}&page={page}&spid={spid}&product_id={product_id}&seller_id={seller_id}"
        response = requests.get(api_url, headers=headers)

        if response.status_code == 200:
            data = response.json()
            reviews = data.get("data", [])
            all_reviews.extend(reviews)
            print(f"Đã lấy {len(reviews)} review từ trang {page}/{last_page}")
        else:
            print(f"Lỗi khi lấy trang {page}: {response.status_code}")

        time.sleep(1)  # Tránh bị chặn

    # Lưu vào CSV
    save_reviews_to_csv(all_reviews, output_file)
    print(f"Tổng số review đã lưu: {len(all_reviews)}")

# Hàm lưu dữ liệu vào file CSV
def save_reviews_to_csv(reviews, filename):
    with open(filename, mode="w", newline="", encoding="utf-8-sig") as file:
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
    print(f"Dữ liệu đã lưu vào {filename}")

# Chạy chương trình
if __name__ == "__main__":
    product_url = input("🔗 Nhập link sản phẩm Tiki: ").strip()
    product_id, spid = extract_tiki_ids(product_url)

    if not product_id:
        print("Không tìm thấy product_id trong URL!")
    else:
        product_name = get_product_name(product_id)
        print(f"Tên sản phẩm: {product_name}")

        if not spid:
            print("Không tìm thấy spid trong URL, đang tìm kiếm trên API...")
            spid = get_spid_if_missing(product_id)

        if not spid:
            print("Không lấy được spid, không thể tiếp tục!")
        else:
            seller_id = get_seller_id(product_id, spid)
            print(f"Tự động lấy: product_id={product_id}, spid={spid}, seller_id={seller_id}")

            output_file = f"reviews_{product_id}.csv"
            crawl_reviews(product_id, spid, seller_id, output_file)
