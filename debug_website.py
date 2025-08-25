import os
import time
import pandas as pd
import re
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options

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

def debug_website(driver, url):
    """Debug website to understand its structure"""
    
    try:
        print(f"Đang truy cập: {url}")
        driver.get(url)
        time.sleep(10)  # Chờ lâu hơn
        
        # Scroll to trigger lazy loading
        driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
        time.sleep(5)
        driver.execute_script("window.scrollTo(0, 0);")
        time.sleep(5)
        
        # Get page title
        title = driver.title
        print(f"Tiêu đề trang: {title}")
        
        # Get all text from page
        page_text = driver.find_element(By.TAG_NAME, "body").text
        print(f"Độ dài text trang: {len(page_text)} ký tự")
        
        # Save page text to file for inspection
        with open("page_content.txt", "w", encoding="utf-8") as f:
            f.write(page_text)
        print("Đã lưu nội dung trang vào file page_content.txt")
        
        # Look for part numbers with different patterns
        patterns = [
            r'[A-Z0-9\-]+ZZ',
            r'[A-Z0-9\-]+',
            r'\d{4}ZZ',
            r'\d{4}',
            r'[A-Z]{2,4}\d{2,4}ZZ'
        ]
        
        for pattern in patterns:
            matches = re.findall(pattern, page_text)
            unique_matches = list(set(matches))
            print(f"Pattern '{pattern}': Tìm thấy {len(unique_matches)} kết quả")
            if len(unique_matches) > 0 and len(unique_matches) < 20:
                print(f"  Các kết quả: {unique_matches[:10]}")
        
        # Look for tables
        tables = driver.find_elements(By.TAG_NAME, "table")
        print(f"Tìm thấy {len(tables)} bảng")
        
        for i, table in enumerate(tables):
            try:
                rows = table.find_elements(By.TAG_NAME, "tr")
                print(f"Bảng {i+1}: {len(rows)} hàng")
                
                if len(rows) > 0:
                    # Get headers
                    header_row = rows[0]
                    header_cells = header_row.find_elements(By.TAG_NAME, "th")
                    if not header_cells:
                        header_cells = header_row.find_elements(By.TAG_NAME, "td")
                    
                    headers = [cell.text.strip() for cell in header_cells]
                    print(f"  Headers: {headers}")
                    
                    # Show first few rows
                    for j, row in enumerate(rows[1:min(5, len(rows))]):
                        cells = row.find_elements(By.TAG_NAME, "td")
                        row_data = [cell.text.strip() for cell in cells]
                        print(f"  Row {j+1}: {row_data}")
                        
            except Exception as e:
                print(f"Lỗi xử lý bảng {i+1}: {e}")
        
        # Look for price information
        price_patterns = [
            r'\d{1,3}(?:,\d{3})*\s*VND',
            r'\d+\.?\d*\s*VND',
            r'\d{1,3}(?:,\d{3})*\s*₫',
            r'\d+\.?\d*\s*₫',
            r'\d{1,3}(?:,\d{3})*\s*đồng',
            r'\d+\.?\d*\s*đồng'
        ]
        
        for pattern in price_patterns:
            matches = re.findall(pattern, page_text)
            if matches:
                print(f"Tìm thấy giá với pattern '{pattern}': {matches[:5]}")
        
        # Look for shipping information
        shipping_keywords = ['same day', 'ngay', 'day', 'ngày', 'ship', 'giao']
        for keyword in shipping_keywords:
            if keyword.lower() in page_text.lower():
                print(f"Tìm thấy từ khóa giao hàng: '{keyword}'")
        
        # Look for quantity information
        qty_patterns = [
            r'\d+\s*piece',
            r'\d+\s*cái',
            r'\d+\s*chiếc',
            r'\d+\s*pcs',
            r'\d+\s*pc'
        ]
        
        for pattern in qty_patterns:
            matches = re.findall(pattern, page_text.lower())
            if matches:
                print(f"Tìm thấy số lượng với pattern '{pattern}': {matches[:5]}")
        
        return page_text
        
    except Exception as e:
        print(f"Lỗi debug website: {e}")
        return None

def main():
    # URL cụ thể mà user muốn crawl
    target_url = "https://vn.misumi-ec.com/vona2/detail/110310367019/?KWSearch=bearing&searchFlow=results2products&list=PageSearchResult"
    
    print(f"Bắt đầu debug website: {target_url}")
    
    # Setup driver
    driver = setup_driver()
    if not driver:
        print("Không thể khởi tạo Chrome driver")
        return
    
    try:
        # Debug the website
        page_text = debug_website(driver, target_url)
        
        if page_text:
            print("\nDebug hoàn thành!")
            print("Kiểm tra file page_content.txt để xem nội dung trang")
        else:
            print("Không thể lấy nội dung trang")
            
    finally:
        # Keep browser open for manual inspection
        input("Nhấn Enter để đóng trình duyệt...")
        driver.quit()

if __name__ == "__main__":
    main()
