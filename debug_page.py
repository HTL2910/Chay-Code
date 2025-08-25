import os
import time
import pandas as pd
import re
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
from selenium.common.exceptions import TimeoutException, NoSuchElementException

def setup_driver():
    chrome_options = Options()
    # chrome_options.add_argument("--headless")  # Tạm thời bỏ headless để debug
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    chrome_options.add_argument("--disable-gpu")
    chrome_options.add_argument("--window-size=1920,1080")
    chrome_options.add_argument("--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36")
    try:
        driver = webdriver.Chrome(options=chrome_options)
        return driver
    except Exception as e:
        print(f"Error setting up Chrome driver: {e}")
        return None

def debug_page(driver, url):
    """Debug trang web để hiểu cấu trúc"""
    try:
        print(f"Đang truy cập: {url}")
        driver.get(url)
        time.sleep(10)  # Đợi lâu hơn
        
        # Lấy thông tin cơ bản
        print(f"Title: {driver.title}")
        print(f"URL hiện tại: {driver.current_url}")
        
        # Kiểm tra nội dung trang
        body_text = driver.find_element(By.TAG_NAME, "body").text
        print(f"Độ dài nội dung: {len(body_text)} ký tự")
        print(f"100 ký tự đầu: {body_text[:100]}")
        
        # Tìm tất cả các bảng
        tables = driver.find_elements(By.TAG_NAME, "table")
        print(f"Số lượng bảng: {len(tables)}")
        
        for i, table in enumerate(tables):
            print(f"\n--- Bảng {i+1} ---")
            try:
                rows = table.find_elements(By.TAG_NAME, "tr")
                print(f"Số hàng: {len(rows)}")
                
                if len(rows) > 0:
                    # Lấy header
                    header_cells = rows[0].find_elements(By.TAG_NAME, "th")
                    if not header_cells:
                        header_cells = rows[0].find_elements(By.TAG_NAME, "td")
                    
                    headers = [cell.text.strip() for cell in header_cells]
                    print(f"Headers: {headers}")
                    
                    # Lấy một vài hàng đầu
                    for j in range(1, min(4, len(rows))):
                        cells = rows[j].find_elements(By.TAG_NAME, "td")
                        row_data = [cell.text.strip() for cell in cells]
                        print(f"Hàng {j}: {row_data}")
                        
            except Exception as e:
                print(f"Lỗi xử lý bảng {i+1}: {e}")
        
        # Tìm part numbers
        part_numbers = re.findall(r'[A-Z0-9\-]+ZZ', body_text)
        unique_part_numbers = list(set(part_numbers))
        print(f"\nPart numbers tìm thấy: {unique_part_numbers}")
        
        # Tìm giá
        price_patterns = [
            r'(\d{1,3}(?:,\d{3})*\s*VND)',
            r'(\d+\.?\d*\s*VND)',
            r'(\d{1,3}(?:,\d{3})*\s*₫)',
            r'(\d+\.?\d*\s*₫)',
        ]
        
        for pattern in price_patterns:
            prices = re.findall(pattern, body_text)
            if prices:
                print(f"Giá tìm thấy: {prices[:5]}")  # Chỉ hiển thị 5 giá đầu
                break
        
        # Lưu nội dung trang để kiểm tra
        with open("debug_page_content.txt", "w", encoding="utf-8") as f:
            f.write(body_text)
        print(f"\nĐã lưu nội dung trang vào debug_page_content.txt")
        
        # Chụp ảnh màn hình
        driver.save_screenshot("debug_screenshot.png")
        print(f"Đã chụp ảnh màn hình: debug_screenshot.png")
        
    except Exception as e:
        print(f"Lỗi debug: {e}")

def main():
    target_url = "https://vn.misumi-ec.com/vona2/detail/110310367019/?KWSearch=bearing&searchFlow=results2products&list=PageSearchResult"
    
    print(f"Bắt đầu debug trang: {target_url}")
    
    driver = setup_driver()
    if not driver:
        print("Không thể khởi tạo Chrome driver")
        return
    
    try:
        debug_page(driver, target_url)
    finally:
        driver.quit()

if __name__ == "__main__":
    main()
