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

def handle_cookies_and_popups(driver):
    """Handle cookies, popups and other dialogs"""
    try:
        print("Đang xử lý cookies và popup...")
        
        # Wait for page to load
        time.sleep(3)
        
        # Try to find and click cookie accept buttons by text
        try:
            # Look for buttons with common cookie accept text
            buttons = driver.find_elements(By.TAG_NAME, "button")
            for button in buttons:
                button_text = button.text.lower()
                if any(keyword in button_text for keyword in ['accept', 'agree', 'ok', 'đồng ý', 'chấp nhận', 'cookie']):
                    try:
                        button.click()
                        print(f"Đã click button: {button.text}")
                        time.sleep(1)
                        break
                    except:
                        continue
        except:
            pass
        
        # Try to find and click close buttons
        try:
            close_buttons = driver.find_elements(By.CSS_SELECTOR, "button[aria-label*='Close'], button[title*='Close'], .close, .modal-close, .popup-close")
            for button in close_buttons:
                try:
                    button.click()
                    print("Đã đóng popup/modal")
                    time.sleep(1)
                except:
                    continue
        except:
            pass
        
        # Try to remove overlays using JavaScript
        try:
            driver.execute_script("""
                var overlays = document.querySelectorAll('.overlay, .modal-backdrop, .popup-overlay, .modal, .popup');
                for(var i = 0; i < overlays.length; i++) {
                    overlays[i].style.display = 'none';
                }
            """)
            print("Đã ẩn overlays bằng JavaScript")
        except:
            pass
            
    except Exception as e:
        print(f"Lỗi xử lý cookies/popup: {e}")

def extract_data_from_url(driver, url):
    """Extract data from specific URL"""
    data = []
    
    try:
        print(f"Đang truy cập: {url}")
        driver.get(url)
        time.sleep(10)  # Đợi lâu hơn để JavaScript load
        
        # Đợi cho trang load xong
        try:
            WebDriverWait(driver, 20).until(
                EC.presence_of_element_located((By.TAG_NAME, "table"))
            )
            print("Đã tìm thấy bảng dữ liệu")
        except TimeoutException:
            print("Không tìm thấy bảng, thử đợi thêm...")
            time.sleep(10)
        
        # Handle cookies and popups
        try:
            # Try to find and click cookie accept buttons by text
            buttons = driver.find_elements(By.TAG_NAME, "button")
            for button in buttons:
                button_text = button.text.lower()
                if any(keyword in button_text for keyword in ['accept', 'agree', 'ok', 'đồng ý', 'chấp nhận', 'cookie']):
                    try:
                        button.click()
                        print(f"Đã click button: {button.text}")
                        time.sleep(1)
                        break
                    except:
                        continue
        except:
            pass
        
        # Try to remove overlays using JavaScript
        try:
            driver.execute_script("""
                var overlays = document.querySelectorAll('.overlay, .modal-backdrop, .popup-overlay, .modal, .popup');
                for(var i = 0; i < overlays.length; i++) {
                    overlays[i].style.display = 'none';
                }
            """)
            print("Đã ẩn overlays bằng JavaScript")
        except:
            pass
        
        # Scroll to trigger lazy loading
        driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
        time.sleep(5)
        driver.execute_script("window.scrollTo(0, 0);")
        time.sleep(5)
        
        # Kiểm tra lại nội dung trang
        page_text = driver.find_element(By.TAG_NAME, "body").text
        print(f"Độ dài nội dung sau khi load: {len(page_text)} ký tự")
        
        # Get all part numbers from the page
        all_part_numbers = re.findall(r'[A-Z0-9\-]+ZZ', page_text)
        unique_part_numbers = list(set(all_part_numbers))
        
        print(f"Tìm thấy {len(unique_part_numbers)} part number duy nhất")
        
        if not unique_part_numbers:
            print("Không tìm thấy part number nào, thử tìm pattern khác...")
            # Thử tìm pattern khác cho part number
            all_part_numbers = re.findall(r'[A-Z0-9\-]+', page_text)
            unique_part_numbers = [p for p in set(all_part_numbers) if len(p) >= 6]  # Lọc các part number có độ dài hợp lý
            print(f"Tìm thấy {len(unique_part_numbers)} part number với pattern khác")
        
        # For each part number, extract complete data
        for part_number in unique_part_numbers:
            row_data = {
                'part_number': part_number,
                'price': '',
                'days_to_ship': '',
                'minimum_order_qty': '',
                'inner_dia_d': '',
                'outer_dia_d': '',
                'width_b': '',
                'basic_load_rating_cr': '',
                'basic_load_rating_cor': '',
                'weight': '',
                'page_url': url
            }
            
            # Find context around this part number
            part_index = page_text.find(part_number)
            if part_index != -1:
                # Get 2000 characters around the part number for better context
                start = max(0, part_index - 1000)
                end = min(len(page_text), part_index + len(part_number) + 1000)
                context = page_text[start:end]
                
                # Extract price from context - cải thiện regex
                price_patterns = [
                    r'(\d{1,3}(?:,\d{3})*\s*VND)',
                    r'(\d+\.?\d*\s*VND)',
                    r'(\d{1,3}(?:,\d{3})*\s*₫)',
                    r'(\d+\.?\d*\s*₫)',
                    r'(\d{1,3}(?:,\d{3})*\s*đồng)',
                    r'(\d+\.?\d*\s*đồng)'
                ]
                
                for pattern in price_patterns:
                    price_match = re.search(pattern, context)
                    if price_match:
                        row_data['price'] = price_match.group(1)
                        break
                
                # Extract days to ship from context - cải thiện
                if 'same day' in context.lower() or 'ngay' in context.lower():
                    row_data['days_to_ship'] = 'same day'
                elif 'day' in context.lower() or 'ngày' in context.lower():
                    day_match = re.search(r'(\d+\s*(?:day|ngày))', context.lower())
                    if day_match:
                        row_data['days_to_ship'] = day_match.group(1)
                
                # Extract minimum order quantity from context - cải thiện
                qty_patterns = [
                    r'(\d+\s*piece)',
                    r'(\d+\s*cái)',
                    r'(\d+\s*chiếc)',
                    r'(\d+\s*pcs)',
                    r'(\d+\s*pc)'
                ]
                
                for pattern in qty_patterns:
                    qty_match = re.search(pattern, context.lower())
                    if qty_match:
                        row_data['minimum_order_qty'] = qty_match.group(1)
                        break
            
            # Extract technical specifications from tables - cải thiện
            tables = driver.find_elements(By.TAG_NAME, "table")
            for table in tables:
                try:
                    rows = table.find_elements(By.TAG_NAME, "tr")
                    if len(rows) < 2:
                        continue
                    
                    # Get headers
                    headers = []
                    header_row = rows[0]
                    header_cells = header_row.find_elements(By.TAG_NAME, "th")
                    if not header_cells:
                        header_cells = header_row.find_elements(By.TAG_NAME, "td")
                    
                    for cell in header_cells:
                        headers.append(cell.text.strip().lower())
                    
                    print(f"Headers của bảng: {headers}")
                    
                    # Look for rows containing the part number
                    for row in rows[1:]:
                        cells = row.find_elements(By.TAG_NAME, "td")
                        if not cells:
                            continue
                        
                        row_text = ' '.join([cell.text.strip() for cell in cells])
                        if part_number in row_text:
                            print(f"Tìm thấy part number {part_number} trong hàng: {row_text}")
                            
                            # Extract technical data with improved mapping
                            for i, cell in enumerate(cells):
                                cell_text = cell.text.strip()
                                if i < len(headers):
                                    header = headers[i]
                                    print(f"  Header {i}: '{header}' = '{cell_text}'")
                                    
                                    # Improved mapping logic based on actual headers
                                    if 'part number' in header:
                                        # Skip part number column
                                        continue
                                    elif 'inner diameter' in header and 'd' in header:
                                        if re.search(r'\d+\.?\d*', cell_text):
                                            row_data['inner_dia_d'] = re.search(r'\d+\.?\d*', cell_text).group()
                                            print(f"    -> inner_dia_d: {row_data['inner_dia_d']}")
                                    elif 'outer diameter' in header and 'd' in header:
                                        if re.search(r'\d+\.?\d*', cell_text):
                                            row_data['outer_dia_d'] = re.search(r'\d+\.?\d*', cell_text).group()
                                            print(f"    -> outer_dia_d: {row_data['outer_dia_d']}")
                                    elif 'width' in header and 'b' in header:
                                        if re.search(r'\d+\.?\d*', cell_text):
                                            row_data['width_b'] = re.search(r'\d+\.?\d*', cell_text).group()
                                            print(f"    -> width_b: {row_data['width_b']}")
                                    elif 'basic rated load' in header:
                                        if re.search(r'\d+\.?\d*', cell_text):
                                            row_data['basic_load_rating_cr'] = re.search(r'\d+\.?\d*', cell_text).group()
                                            print(f"    -> basic_load_rating_cr: {row_data['basic_load_rating_cr']}")
                                    elif 'allowable rotational speed' in header or 'rpm' in header:
                                        # This is RPM, not load rating
                                        continue
                                    elif 'weight' in header and 'g' in header:
                                        if re.search(r'\d+\.?\d*', cell_text):
                                            row_data['weight'] = re.search(r'\d+\.?\d*', cell_text).group()
                                            print(f"    -> weight: {row_data['weight']}")
                                    elif 'mounting dimensions' in header:
                                        # This is mounting dimensions, not load rating
                                        continue
                                    elif 'r\n(min.)' in header:
                                        # This is minimum radius, not load rating
                                        continue
                            
                            break  # Found the row, no need to continue
                            
                except Exception as e:
                    print(f"Lỗi xử lý bảng: {e}")
                    continue
            
            # Tìm kiếm giá và tải trọng tĩnh từ các bảng khác
            if not row_data['price'] or not row_data['basic_load_rating_cor']:
                # Tìm kiếm trong tất cả các bảng
                all_tables = driver.find_elements(By.TAG_NAME, "table")
                for table in all_tables:
                    try:
                        rows = table.find_elements(By.TAG_NAME, "tr")
                        if len(rows) < 2:
                            continue
                        
                        # Get headers
                        headers = []
                        header_row = rows[0]
                        header_cells = header_row.find_elements(By.TAG_NAME, "th")
                        if not header_cells:
                            header_cells = header_row.find_elements(By.TAG_NAME, "td")
                        
                        for cell in header_cells:
                            headers.append(cell.text.strip().lower())
                        
                        # Look for rows containing the part number
                        for row in rows[1:]:
                            cells = row.find_elements(By.TAG_NAME, "td")
                            if not cells:
                                continue
                            
                            row_text = ' '.join([cell.text.strip() for cell in cells])
                            if part_number in row_text:
                                # Tìm giá trong hàng này
                                if not row_data['price']:
                                    for i, cell in enumerate(cells):
                                        cell_text = cell.text.strip()
                                        # Tìm giá với các pattern khác nhau
                                        price_patterns = [
                                            r'(\d{1,3}(?:,\d{3})*\s*VND)',
                                            r'(\d+\.?\d*\s*VND)',
                                            r'(\d{1,3}(?:,\d{3})*\s*₫)',
                                            r'(\d+\.?\d*\s*₫)',
                                            r'(\d{1,3}(?:,\d{3})*\s*đồng)',
                                            r'(\d+\.?\d*\s*đồng)',
                                            r'(\d{1,3}(?:,\d{3})*)',  # Số có dấu phẩy
                                        ]
                                        
                                        for pattern in price_patterns:
                                            price_match = re.search(pattern, cell_text)
                                            if price_match:
                                                row_data['price'] = price_match.group(1)
                                                print(f"    -> Tìm thấy giá: {row_data['price']}")
                                                break
                                
                                # Tìm tải trọng tĩnh
                                if not row_data['basic_load_rating_cor']:
                                    for i, cell in enumerate(cells):
                                        cell_text = cell.text.strip()
                                        if i < len(headers):
                                            header = headers[i]
                                            # Tìm tải trọng tĩnh trong các header khác nhau
                                            if any(keyword in header for keyword in ['static', 'cor', 'tĩnh', 'static load', 'static rated load']):
                                                if re.search(r'\d+\.?\d*', cell_text):
                                                    row_data['basic_load_rating_cor'] = re.search(r'\d+\.?\d*', cell_text).group()
                                                    print(f"    -> Tìm thấy tải trọng tĩnh: {row_data['basic_load_rating_cor']}")
                                                    break
                                
                                break  # Found the row, no need to continue
                                
                    except Exception as e:
                        print(f"Lỗi xử lý bảng bổ sung: {e}")
                        continue
            
            # Thêm logic tìm kiếm trong toàn bộ trang cho các thông tin còn thiếu
            if not row_data['price'] or not row_data['days_to_ship'] or not row_data['minimum_order_qty']:
                # Tìm kiếm trong toàn bộ trang
                full_page_text = driver.find_element(By.TAG_NAME, "body").text
                
                # Tìm giá trong toàn bộ trang - cải thiện
                if not row_data['price']:
                    # Tìm giá gần part number
                    part_context_start = max(0, page_text.find(part_number) - 2000)
                    part_context_end = min(len(page_text), page_text.find(part_number) + len(part_number) + 2000)
                    part_context = page_text[part_context_start:part_context_end]
                    
                    price_patterns = [
                        r'(\d{1,3}(?:,\d{3})*\s*VND)',
                        r'(\d+\.?\d*\s*VND)',
                        r'(\d{1,3}(?:,\d{3})*\s*₫)',
                        r'(\d+\.?\d*\s*₫)',
                        r'(\d{1,3}(?:,\d{3})*\s*đồng)',
                        r'(\d+\.?\d*\s*đồng)'
                    ]
                    
                    for pattern in price_patterns:
                        price_matches = re.findall(pattern, part_context)
                        if price_matches:
                            # Lấy giá đầu tiên tìm thấy
                            row_data['price'] = price_matches[0]
                            print(f"Tìm thấy giá cho {part_number}: {row_data['price']}")
                            break
                
                # Tìm thời gian giao hàng
                if not row_data['days_to_ship']:
                    if 'same day' in full_page_text.lower() or 'ngay' in full_page_text.lower():
                        row_data['days_to_ship'] = 'same day'
                    else:
                        day_match = re.search(r'(\d+\s*(?:day|ngày))', full_page_text.lower())
                        if day_match:
                            row_data['days_to_ship'] = day_match.group(1)
                
                # Tìm số lượng đặt hàng tối thiểu
                if not row_data['minimum_order_qty']:
                    qty_patterns = [
                        r'(\d+\s*piece)',
                        r'(\d+\s*cái)',
                        r'(\d+\s*chiếc)',
                        r'(\d+\s*pcs)',
                        r'(\d+\s*pc)'
                    ]
                    
                    for pattern in qty_patterns:
                        qty_match = re.search(pattern, full_page_text.lower())
                        if qty_match:
                            row_data['minimum_order_qty'] = qty_match.group(1)
                            break
            
            # Only add if we have at least some data
            if any([row_data['price'], row_data['days_to_ship'], row_data['minimum_order_qty'], 
                   row_data['inner_dia_d'], row_data['outer_dia_d'], row_data['width_b'], 
                   row_data['basic_load_rating_cr'], row_data['basic_load_rating_cor'], row_data['weight']]):
                data.append(row_data)
                print(f"Đã trích xuất: {part_number} - Giá: {row_data['price']} - Ngày giao: {row_data['days_to_ship']} - Số lượng tối thiểu: {row_data['minimum_order_qty']} - Đường kính trong: {row_data['inner_dia_d']} - Đường kính ngoài: {row_data['outer_dia_d']} - Độ dày: {row_data['width_b']} - Tải động: {row_data['basic_load_rating_cr']} - Tải tĩnh: {row_data['basic_load_rating_cor']} - Trọng lượng: {row_data['weight']}")
        
        print(f"Tổng cộng trích xuất: {len(data)} dòng từ {url}")
        
    except Exception as e:
        print(f"Lỗi trích xuất dữ liệu từ {url}: {e}")
        
    return data

def main():
    # URL cụ thể mà user muốn crawl
    target_url = "https://vn.misumi-ec.com/vona2/detail/110310367019/?KWSearch=bearing&searchFlow=results2products&list=PageSearchResult"
    
    print(f"Bắt đầu crawl dữ liệu từ URL: {target_url}")
    
    # Setup driver
    driver = setup_driver()
    if not driver:
        print("Không thể khởi tạo Chrome driver")
        return
    
    try:
        # Extract data from the specific URL
        data = extract_data_from_url(driver, target_url)
        
        if data:
            # Create DataFrame and remove duplicates
            df_result = pd.DataFrame(data)
            df_result = df_result.drop_duplicates(subset=['part_number'], keep='first')
            
            print(f"\nKết quả cuối cùng:")
            print(f"Tổng số part number duy nhất: {len(df_result)}")
            print(f"Part number có giá: {len(df_result[df_result['price'] != ''])}")
            print(f"Part number có thời gian giao hàng: {len(df_result[df_result['days_to_ship'] != ''])}")
            print(f"Part number có số lượng đặt hàng tối thiểu: {len(df_result[df_result['minimum_order_qty'] != ''])}")
            print(f"Part number có đường kính trong: {len(df_result[df_result['inner_dia_d'] != ''])}")
            print(f"Part number có đường kính ngoài: {len(df_result[df_result['outer_dia_d'] != ''])}")
            print(f"Part number có độ dày: {len(df_result[df_result['width_b'] != ''])}")
            print(f"Part number có tải trọng động (Cr): {len(df_result[df_result['basic_load_rating_cr'] != ''])}")
            print(f"Part number có tải trọng tĩnh (Cor): {len(df_result[df_result['basic_load_rating_cor'] != ''])}")
            print(f"Part number có trọng lượng: {len(df_result[df_result['weight'] != ''])}")
            
            # Save results
            output_csv = "retry_specific_url_data.csv"
            output_excel = "retry_specific_url_data.xlsx"
            
            df_result.to_csv(output_csv, index=False)
            df_result.to_excel(output_excel, index=False)
            
            print(f"\nĐã lưu kết quả vào:")
            print(f"CSV: {output_csv}")
            print(f"Excel: {output_excel}")
            
            # Show sample data
            print("\nDữ liệu mẫu:")
            print(df_result.head(10).to_string())
            
        else:
            print("Không có dữ liệu được trích xuất")
            
    finally:
        driver.quit()

if __name__ == "__main__":
    main()
