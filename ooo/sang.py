import time
import pandas as pd
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
from bs4 import BeautifulSoup

def setup_driver():
    chrome_options = Options()
    chrome_options.add_argument("--headless")
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

# ====== HÀM LẤY DANH SÁCH PART NUMBER ======
def extract_all_part_numbers(driver):
    wait = WebDriverWait(driver, 60)
    time.sleep(5)
    # Scroll to trigger lazy loading
    driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
    time.sleep(2)
    driver.execute_script("window.scrollTo(0, 0);")
    time.sleep(2)

    # Chờ đúng nút có id 'codeList'
    dropdown_btn = wait.until(EC.element_to_be_clickable((By.XPATH, "//*[@id='detailTabs']/div/div/div/ul/li[2]")))
    time.sleep(5)
    dropdown_btn.click()
    time.sleep(5)

    part_numbers=[]
    link_numbers=[]
    table_part_number=wait.until(EC.presence_of_element_located((By.CLASS_NAME, "PartNumberColumn_tableBase__DK2Le")))
    
    part_elements = table_part_number.find_elements(By.CLASS_NAME, "PartNumberColumn_dataRow__43D6Y")
    
    for element in part_elements:
        a_elements = element.find_elements(By.TAG_NAME, "a")
        title = a_elements[0].get_attribute("title")
        link = a_elements[0].get_attribute("href")
        part_numbers.append(title)
        link_numbers.append(link)
    print("part_numbers:", part_numbers)
    print("link_numbers:", link_numbers)
    return part_numbers, link_numbers


def get_data_prices_days_ship(driver):
    wait = WebDriverWait(driver, 60)
    time.sleep(5)
    # Scroll to trigger lazy loading
    driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
    time.sleep(2)
    driver.execute_script("window.scrollTo(0, 0);")
    time.sleep(2)

    # Chờ đúng nút có id 'codeList'
    dropdown_btn = wait.until(EC.element_to_be_clickable((By.XPATH, "//*[@id='detailTabs']/div/div/div/ul/li[2]")))
    time.sleep(5)
    dropdown_btn.click()
    time.sleep(5)
    prices=[]
    days_to_ship=[]
    table_price_days_ship=wait.until(EC.presence_of_element_located((By.CLASS_NAME, "PartNumberAsideColumns_table__6fKVE")))
    rows=table_price_days_ship.find_elements(By.CLASS_NAME, "PartNumberAsideColumns_dataRow__OUw8N")
    for row in rows:
        #lấy giá
        price_cell=row.find_element(By.CLASS_NAME, "PartNumberAsideColumns_dataCellBase__tIm9A")
        price=price_cell.find_element(By.CLASS_NAME, "PartNumberAsideColumns_data__jikjP").find_element(By.TAG_NAME, "span").text.strip()
        prices.append(price)
        #lấy ngày giao hàng
        day_to_ship_cell=row.find_element(By.CLASS_NAME, "PartNumberAsideColumns_daysToShipDataCell__JRaMu")
        day_to_ship=day_to_ship_cell.find_element(By.CLASS_NAME, "PartNumberAsideColumns_data__jikjP").find_element(By.TAG_NAME, "span").text.strip()
        days_to_ship.append(day_to_ship)
    print("prices:", prices)
    print("days_to_ship:", days_to_ship)
    return prices, days_to_ship
def get_other_data(driver):
    wait = WebDriverWait(driver, 60)
    time.sleep(5)
    driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
    time.sleep(2)
    driver.execute_script("window.scrollTo(0, 0);")
    time.sleep(2)
    
    print("Trying to click dropdown button...")
    try:
        dropdown_btn = wait.until(EC.element_to_be_clickable((By.XPATH, "//*[@id='detailTabs']/div/div/div/ul/li[2]")))
        time.sleep(5)
        dropdown_btn.click()
        time.sleep(5)
        print("Successfully clicked dropdown button")
    except Exception as e:
        print(f"Could not click dropdown button: {e}")
        # Thử tìm nút khác
        try:
            print("Trying alternative dropdown selector...")
            dropdown_btn = wait.until(EC.element_to_be_clickable((By.XPATH, "//li[contains(text(), 'Part Number')]")))
            dropdown_btn.click()
            time.sleep(5)
            print("Successfully clicked alternative dropdown button")
        except Exception as e2:
            print(f"Alternative dropdown also failed: {e2}")
            return {}
    
    ####################################Get name columns
    print("Trying to extract table headers...")
    try:
        table_header = wait.until(EC.presence_of_element_located(
            (By.CLASS_NAME, "PartNumberSpecHeader_tableBase__Y5X_f")
        ))
        cols_header = table_header.find_elements(By.CLASS_NAME, "PartNumberSpecHeader_headerCell__r3GLv")
        print(f"Found {len(cols_header)} header columns")

        table_heade_data = {}

        for i, col in enumerate(cols_header):
            html = col.get_attribute("innerHTML")
            soup = BeautifulSoup(html, "html.parser")
            # lấy toàn bộ text trong cell, kể cả <div>, <p>, text thô
            header_text = soup.get_text(" ", strip=True)
            if header_text:  # Only add non-empty headers
                table_heade_data[header_text] = []
                print(f"Header {i+1}: '{header_text}'")
    except Exception as e:
        print(f"Could not extract table headers: {e}")
        # Thử tìm bảng khác
        try:
            print("Trying alternative table header selector...")
            table_header = wait.until(EC.presence_of_element_located(
                (By.CSS_SELECTOR, "[class*='PartNumberSpecHeader']")
            ))
            cols_header = table_header.find_elements(By.CSS_SELECTOR, "[class*='headerCell']")
            print(f"Found {len(cols_header)} header columns with alternative selector")
            
            table_heade_data = {}
            for i, col in enumerate(cols_header):
                header_text = col.text.strip()
                if header_text:
                    table_heade_data[header_text] = []
                    print(f"Header {i+1}: '{header_text}'")
        except Exception as e2:
            print(f"Alternative header extraction also failed: {e2}")
            return {}

    ####################################Get data rows
    print("Trying to extract table data...")
    try:
        table_other_data = wait.until(
            EC.presence_of_element_located((By.CLASS_NAME, "PartNumberSpecColumns_tableBase__VK5Nd"))
        )

        rows = table_other_data.find_elements(By.CLASS_NAME, "PartNumberSpecColumns_dataRow__M4B4a")
        print(f"Found {len(rows)} data rows")

        for row_idx, row in enumerate(rows):
            html = row.get_attribute("innerHTML")
            soup = BeautifulSoup(html, "html.parser")
            values = [div.get_text(strip=True) for div in soup.select("div.PartNumberSpecCells_data__u6ZZX")]
            print(f"Row {row_idx+1}: {len(values)} values")
            
            # Fix: Convert keys to list before indexing
            header_keys = list(table_heade_data.keys())
            for i in range(len(header_keys)):
                if i < len(values):  # Add bounds checking
                    table_heade_data[header_keys[i]].append(values[i])
                else:
                    table_heade_data[header_keys[i]].append('')  # Fill empty values
    except Exception as e:
        print(f"Could not extract table data: {e}")
        # Thử tìm bảng dữ liệu khác
        try:
            print("Trying alternative table data selector...")
            table_other_data = wait.until(
                EC.presence_of_element_located((By.CSS_SELECTOR, "[class*='PartNumberSpecColumns']"))
            )
            rows = table_other_data.find_elements(By.CSS_SELECTOR, "[class*='dataRow']")
            print(f"Found {len(rows)} data rows with alternative selector")
            
            for row_idx, row in enumerate(rows):
                cells = row.find_elements(By.CSS_SELECTOR, "[class*='data']")
                values = [cell.text.strip() for cell in cells]
                print(f"Row {row_idx+1}: {len(values)} values")
                
                header_keys = list(table_heade_data.keys())
                for i in range(len(header_keys)):
                    if i < len(values):
                        table_heade_data[header_keys[i]].append(values[i])
                    else:
                        table_heade_data[header_keys[i]].append('')
        except Exception as e2:
            print(f"Alternative data extraction also failed: {e2}")
            return {}

    print(f"Final table_heade_data: {len(table_heade_data)} columns")
    for key, values in table_heade_data.items():
        print(f"  {key}: {len(values)} values")
    return table_heade_data
def get_url_From_file(file_path,start_index,end_index):
    try:
        df = pd.read_csv(file_path)
        if 'Product URL' in df.columns:
            urls = df['Product URL'].tolist()
            # Add bounds checking
            if start_index < 0:
                start_index = 0
            if end_index > len(urls):
                end_index = len(urls)
            if start_index >= end_index:
                print("⚠ Invalid index range: start_index >= end_index")
                return []
            return urls[start_index:end_index]
        else:
            print("⚠ 'Product URL' column not found in the CSV file.")
            print(f"Available columns: {list(df.columns)}")
            return []
    except FileNotFoundError:
        print(f"⚠ File not found: {file_path}")
        return []
    except Exception as e:
        print(f"⚠ Error reading file {file_path}: {e}")
        return []
def get_data_from_url(driver, url):
    try:
        driver.get(url)
        time.sleep(5)
        
        # Check if page loaded successfully
        if "misumi-ec.com" not in driver.current_url:
            print(f"Page redirect detected. Current URL: {driver.current_url}")
            
        # part_numbers, link_numbers = extract_all_part_numbers(driver)
        # prices, days_to_ship = get_data_prices_days_ship(driver)
        part_numbers=[]
        link_numbers=[]
        prices=[]
        days_to_ship=[]
        
        table_heade_data = get_other_data(driver)
        
        # Add debugging information
        if table_heade_data:
            print(f"Successfully extracted data with {len(table_heade_data)} columns")
            for key, values in table_heade_data.items():
                print(f"  {key}: {len(values)} values")
        else:
            print("No data extracted from this URL")
            
        return table_heade_data
        
    except Exception as e:
        print(f"Error in get_data_from_url: {e}")
        return {}

def validate_data_consistency(all_combined_data):
    """Kiểm tra tính nhất quán của dữ liệu"""
    if not all_combined_data:
        return False
    
    # Kiểm tra tất cả các cột có cùng độ dài
    lengths = [len(values) for values in all_combined_data.values()]
    if len(set(lengths)) != 1:
        print(f"⚠ Lỗi: Các cột có độ dài khác nhau: {lengths}")
        return False
    
    print(f"✅ Tất cả {len(all_combined_data)} cột đều có {lengths[0]} rows")
    return True

def print_data_processing_info(url, url_data, all_combined_data, total_rows_processed, url_row_count):
    """In thông tin chi tiết về quá trình xử lý dữ liệu"""
    print(f"\n=== Thông tin xử lý URL: {url} ===")
    print(f"Số rows từ URL này: {url_row_count}")
    print(f"Tổng rows đã xử lý trước đó: {total_rows_processed}")
    print(f"Số cột từ URL này: {len(url_data)}")
    print(f"Số cột trong dữ liệu tổng hợp: {len(all_combined_data)}")
    
    # Kiểm tra cột mới
    new_columns = [key for key in url_data.keys() if key not in all_combined_data]
    if new_columns:
        print(f"Cột mới được thêm: {new_columns}")
    
    # Kiểm tra cột thiếu
    missing_columns = [key for key in all_combined_data.keys() if key not in url_data and key != 'Source_URL']
    if missing_columns:
        print(f"Cột thiếu trong URL này: {missing_columns}")
    
    print("=" * 50)

# ====== MAIN ======
def main():
    #2 dòng cần chú ý
    urls = get_url_From_file("same_day_products_from_html.csv",0,3)
    name_file_to_save="input_Name_here"
    #2 dòng cần chú ý
    
    # Initialize data structure to accumulate all data
    all_combined_data = {}
    total_rows_processed = 0
    
    for url in urls:
        print("Processing URL:", url)
        driver = setup_driver()
        if not driver:
            print("Failed to setup Chrome driver")
            continue
            
        try:
            driver.maximize_window()
            url_data = get_data_from_url(driver, url)
            
            # Check if we got any data from this URL
            if not url_data or all(len(values) == 0 for values in url_data.values()):
                print(f"No data extracted from URL: {url}")
                continue
                
            # Get the number of rows from this URL
            url_row_count = max(len(values) for values in url_data.values()) if url_data else 0
            
            if url_row_count == 0:
                print(f"No rows found in data from URL: {url}")
                continue
                
            print(f"Extracted {url_row_count} rows from URL")
            
            # In thông tin chi tiết về quá trình xử lý
            print_data_processing_info(url, url_data, all_combined_data, total_rows_processed, url_row_count)
            
            # Add URL identifier to track data source
            if 'Source_URL' not in all_combined_data:
                all_combined_data['Source_URL'] = []
            all_combined_data['Source_URL'].extend([url] * url_row_count)
            
            # Xử lý các cột mới từ URL hiện tại
            new_columns = []
            for key in url_data.keys():
                if key not in all_combined_data:
                    new_columns.append(key)
                    print(f"Adding new column: {key}")
                    all_combined_data[key] = []
                    # Điền giá trị rỗng cho tất cả dữ liệu cũ (từ các URL trước đó)
                    all_combined_data[key].extend([''] * total_rows_processed)
            
            # Xử lý các cột hiện có trong all_combined_data nhưng không có trong url_data
            missing_columns = []
            for key in all_combined_data.keys():
                if key not in url_data and key != 'Source_URL':
                    missing_columns.append(key)
                    print(f"Column '{key}' missing in current URL, will fill with empty values")
            
            # Đảm bảo tất cả các cột hiện có có đủ số lượng phần tử
            for key in all_combined_data:
                while len(all_combined_data[key]) < total_rows_processed:
                    all_combined_data[key].append('')
            
            # Thêm dữ liệu từ URL hiện tại
            for key, values in url_data.items():
                all_combined_data[key].extend(values)
            
            # Điền giá trị rỗng cho các cột thiếu trong URL hiện tại
            for key in missing_columns:
                all_combined_data[key].extend([''] * url_row_count)
            
            # Update total rows processed
            total_rows_processed += url_row_count
            
            # Đảm bảo tất cả các cột có cùng độ dài
            max_length = max(len(v) for v in all_combined_data.values())
            for key in all_combined_data:
                while len(all_combined_data[key]) < max_length:
                    all_combined_data[key].append('')
                
        except Exception as e:
            print(f"Error processing URL {url}: {e}")
        finally:
            driver.quit()

    print(f"Total rows processed: {total_rows_processed}")
    print("Combined data keys:", list(all_combined_data.keys()))

    # Validate data consistency before saving
    if not validate_data_consistency(all_combined_data):
        print("⚠ Dữ liệu không nhất quán, không thể lưu file")
        return

    # Save the accumulated data
    if all_combined_data and total_rows_processed > 0:
        df = pd.DataFrame(all_combined_data)
        output_file = name_file_to_save+".xlsx"
        df.to_excel(output_file, index=False)
        print(f"✅ Đã lưu dữ liệu vào {output_file}")
        print(f"DataFrame shape: {df.shape}")
        
        # In thống kê về dữ liệu
        print("\nThống kê dữ liệu:")
        for col in df.columns:
            non_empty_count = (df[col] != '').sum()
            print(f"  {col}: {non_empty_count}/{len(df)} rows có dữ liệu")
    else:
        print("⚠ Không lấy được dữ liệu nào.")


if __name__ == "__main__":
    main()