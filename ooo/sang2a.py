import time
import pandas as pd
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options

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
    
    # Wait for page to load completely
    print("Waiting for page to load...")
    time.sleep(10)
    
    # Scroll to trigger lazy loading
    print("Scrolling to trigger lazy loading...")
    driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
    time.sleep(3)
    driver.execute_script("window.scrollTo(0, 0);")
    time.sleep(3)

    # Try multiple selectors for the dropdown button
    dropdown_btn = None
    selectors = [
        "//*[@id='codeList']",
        "//div[contains(@class,'PartNumberDropDownList_partNumberSelection')]",
        "//button[contains(@class,'dropdown')]",
        "//div[contains(@class,'dropdown')]",
        "//*[contains(@class,'codeList')]",
        "//*[contains(@class,'partNumber')]"
    ]
    
    for selector in selectors:
        try:
            print(f"Trying selector: {selector}")
            dropdown_btn = wait.until(EC.element_to_be_clickable((By.XPATH, selector)))
            print(f"Found dropdown button with selector: {selector}")
            break
        except Exception as e:
            print(f"Selector {selector} failed: {e}")
            continue
    
    if not dropdown_btn:
        # If no dropdown found, try to find the table directly
        print("No dropdown button found, trying to locate table directly...")
        try:
            table = wait.until(EC.presence_of_element_located(
                (By.CLASS_NAME, "PartNumberAsideColumns_table__6fKVE"))
            )
            print("Found table directly without dropdown")
        except Exception as e:
            print(f"Could not find table directly: {e}")
            # Try alternative table selectors
            alternative_selectors = [
                "//table[contains(@class,'table')]",
                "//div[contains(@class,'table')]",
                "//*[contains(@class,'PartNumber')]"
            ]
            table = None
            for selector in alternative_selectors:
                try:
                    table = wait.until(EC.presence_of_element_located((By.XPATH, selector)))
                    print(f"Found table with alternative selector: {selector}")
                    break
                except Exception:
                    continue
            
            if not table:
                print("ERROR: Could not find any table or dropdown. Page structure may have changed.")
                return []
    else:
        # Click the dropdown if found
        try:
            print("Clicking dropdown button...")
            dropdown_btn.click()
            time.sleep(5)
        except Exception as e:
            print(f"Error clicking dropdown: {e}")
            # Continue anyway, the table might be visible

    # Try to find the table with multiple selectors
    table = None
    table_selectors = [
        (By.CLASS_NAME, "PartNumberAsideColumns_table__6fKVE"),
        (By.XPATH, "//*[@id='partNumberListTable']/div/div[2]/table"),
        (By.XPATH, "//table[contains(@class,'table')]"),
        (By.XPATH, "//div[contains(@class,'table')]"),
        (By.CSS_SELECTOR, "table"),
        (By.CSS_SELECTOR, "[class*='table']")
    ]
    
    for selector_type, selector in table_selectors:
        try:
            print(f"Trying table selector: {selector}")
            table = wait.until(EC.presence_of_element_located((selector_type, selector)))
            print(f"Found table with selector: {selector}")
            break
        except Exception as e:
            print(f"Table selector {selector} failed: {e}")
            continue
    
    if not table:
        print("ERROR: Could not find any table. Returning empty list.")
        return []

    # Try multiple approaches to find rows
    rows = []
    row_selectors = [
        "tbody tr.PartNumberAsideColumns_dataRow__OUw8N",
        "tbody tr",
        "tr.PartNumberAsideColumns_dataRow__OUw8N",
        "tr[class*='dataRow']",
        "tr"
    ]
    
    for selector in row_selectors:
        try:
            rows = table.find_elements(By.CSS_SELECTOR, selector)
            if rows:
                print(f"Found {len(rows)} rows with selector: {selector}")
                break
        except Exception as e:
            print(f"Row selector {selector} failed: {e}")
            continue
    
    if not rows:
        print("ERROR: Could not find any rows in the table.")
        return []

    part_numbers = []
    prices = []
    days_to_ship = []
    
    print("=== DEBUGGING TABLE STRUCTURE ===")
    # Debug first few rows to understand structure
    for i, row in enumerate(rows[:3]):  # Check first 3 rows
        try:
            cells = row.find_elements(By.TAG_NAME, "td")
            print(f"Row {i} has {len(cells)} cells:")
            for j, cell in enumerate(cells):
                cell_text = cell.text.strip()
                print(f"  Cell {j}: '{cell_text}'")
        except Exception as e:
            print(f"Error debugging row {i}: {e}")
    print("=== END DEBUG ===")
    
    for i, row in enumerate(rows):
        try:
            # Try multiple approaches to extract data
            cells = row.find_elements(By.TAG_NAME, "td")
            if not cells:
                continue
            
            # Find part number - look for cells that look like part numbers
            part_number = ""
            price = ""
            day_to_ship = ""
            
            for j, cell in enumerate(cells):
                cell_text = cell.text.strip()
                if not cell_text:
                    continue
                
                # Part number patterns: usually alphanumeric, may contain dashes, dots
                # Examples: "6200-2RS", "6200ZZ", "6200-2Z", etc.
                if (len(cell_text) >= 4 and 
                    any(char.isdigit() for char in cell_text) and
                    any(char.isalpha() for char in cell_text) and
                    not any(currency in cell_text for currency in ["VND", "$", "¥", "€", "£"]) and
                    not "day" in cell_text.lower() and
                    not "ship" in cell_text.lower() and
                    not "qty" in cell_text.lower() and
                    not "discount" in cell_text.lower()):
                    part_number = cell_text
                    break
            
            # If no part number found in first few cells, try to find it
            if not part_number:
                for j, cell in enumerate(cells[:3]):  # Check first 3 cells
                    cell_text = cell.text.strip()
                    if cell_text and len(cell_text) >= 3:
                        # Skip obvious non-part-numbers
                        if any(currency in cell_text for currency in ["VND", "$", "¥", "€", "£"]):
                            continue
                        if "day" in cell_text.lower() or "ship" in cell_text.lower():
                            continue
                        if cell_text.isdigit() and len(cell_text) <= 3:  # Likely quantity
                            continue
                        part_number = cell_text
                        break
            
            if not part_number:
                print(f"No part number found in row {i}, skipping...")
                continue
                
            # Try to get price - look for currency symbols or VND
            for cell in cells:
                cell_text = cell.text.strip()
                if any(currency in cell_text for currency in ["VND", "$", "¥", "€", "£"]):
                    price = cell_text
                    break
            
            # Try to get days to ship - look for "day" or "ship" keywords
            for cell in cells:
                cell_text = cell.text.strip()
                if "day" in cell_text.lower() or "ship" in cell_text.lower():
                    day_to_ship = cell_text
                    break
            
            part_numbers.append(part_number)
            prices.append(price)
            days_to_ship.append(day_to_ship)
            
        except Exception as e:
            print(f"Error processing row {i}: {e}")
            continue
    
    print("part_numbers:", part_numbers)
    print("prices:", prices)
    print("days_to_ship:", days_to_ship)
    print("part_numbers length:", len(part_numbers))

    return part_numbers


# # ====== HÀM LẤY THÔNG SỐ MỖI PART (có retry) ======
# def extract_specifications(driver, part_number, max_retry=3):
#     wait = WebDriverWait(driver, 60)

#     for attempt in range(1, max_retry + 1):
#         try:
#             # Mở dropdown
#             dropdown_btn = wait.until(EC.element_to_be_clickable(
#                 (By.XPATH, "//div[contains(@class,'PartNumberDropDownList_partNumberSelection')]"))
#             )
#             dropdown_btn.click()
#             time.sleep(3)

#             # Click vào part_number tương ứng
#             option = wait.until(EC.element_to_be_clickable(
#                 (By.XPATH, f"//div[@class='PartNumberDropDownList_partNumberOption__KnDz0' and @title='{part_number}']"))
#             )
#             option.click()
#             time.sleep(6)

#             # Lấy bảng thông số
#             spec_table = wait.until(EC.presence_of_element_located(
#                 (By.CSS_SELECTOR, "div.SpecTable_tableWrapper__TkrZl"))
#             )

#             rows = spec_table.find_elements(By.CSS_SELECTOR, "tr")
#             spec_data = {"Part Number": part_number}

#             for row in rows:
#                 try:
#                     cols = row.find_elements(By.CSS_SELECTOR, "td")
#                     if len(cols) >= 2:
#                         key = cols[0].text.strip()
#                         value = cols[1].text.strip()
#                         spec_data[key] = value
#                 except:
#                     continue

#             # Lấy giá
#             try:
#                 price_elem = driver.find_element(By.CSS_SELECTOR, "span.product_price span")
#                 spec_data["Price"] = price_elem.text.strip()
#             except:
#                 spec_data["Price"] = ""

#             return spec_data

#         except Exception as e:
#             print(f"⚠️ Thử lần {attempt} cho {part_number} thất bại: {e}")
#             if attempt < max_retry:
#                 print("⏳ Thử lại...")
#                 time.sleep(5)
#             else:
#                 print(f"❌ Bỏ qua {part_number} sau {max_retry} lần thử.")
#                 return {"Part Number": part_number, "Error": str(e)}

def get_data_match_part_number(driver, index, part_number):
    wait = WebDriverWait(driver, 60)
    
    # Try multiple selectors for the dropdown button
    dropdown_btn = None
    selectors = [
        "//*[@id='codeList']",
        "//div[contains(@class,'PartNumberDropDownList_partNumberSelection')]",
        "//button[contains(@class,'dropdown')]",
        "//div[contains(@class,'dropdown')]",
        "//*[contains(@class,'codeList')]",
        "//*[contains(@class,'partNumber')]"
    ]
    
    for selector in selectors:
        try:
            print(f"Trying dropdown selector: {selector}")
            dropdown_btn = wait.until(EC.element_to_be_clickable((By.XPATH, selector)))
            print(f"Found dropdown button with selector: {selector}")
            break
        except Exception as e:
            print(f"Dropdown selector {selector} failed: {e}")
            continue
    
    if dropdown_btn:
        try:
            print("Clicking dropdown button...")
            dropdown_btn.click()
            time.sleep(3)
        except Exception as e:
            print(f"Error clicking dropdown for {part_number}: {e}")
    else:
        print(f"No dropdown button found for {part_number}, continuing without dropdown click")

    # Try multiple selectors for the table
    table = None
    table_selectors = [
        (By.XPATH, "//*[@id='partNumberListTable']/div/div[2]/table"),
        (By.CLASS_NAME, "PartNumberAsideColumns_table__6fKVE"),
        (By.XPATH, "//table[contains(@class,'table')]"),
        (By.XPATH, "//div[contains(@class,'table')]"),
        (By.CSS_SELECTOR, "table"),
        (By.CSS_SELECTOR, "[class*='table']")
    ]
    
    for selector_type, selector in table_selectors:
        try:
            print(f"Trying table selector: {selector}")
            table = wait.until(EC.presence_of_element_located((selector_type, selector)))
            print(f"Found table with selector: {selector}")
            break
        except Exception as e:
            print(f"Table selector {selector} failed: {e}")
            continue
    
    if not table:
        print(f"Error locating table for {part_number}")
        return {"Part Number": part_number, "Error": "Table not found"}

    # Find the horizontal scroll container with multiple approaches
    scroll_container = None
    spec_table = None
    
    try:
        scroll_container = driver.find_element(By.CLASS_NAME, "HorizontalScrollbarContainer_contentInner__Nh6zU")
        spec_table = scroll_container.find_element(By.CLASS_NAME, "PartNumberSpecColumns_tableBase__VK5Nd")
    except Exception as e:
        print(f"Error with scroll container for {part_number}: {e}")
        # Try alternative approaches
        try:
            spec_table = driver.find_element(By.CLASS_NAME, "PartNumberSpecColumns_tableBase__VK5Nd")
        except:
            try:
                spec_table = driver.find_element(By.XPATH, "//table[contains(@class,'PartNumberSpec')]")
            except:
                try:
                    spec_table = driver.find_element(By.CSS_SELECTOR, "[class*='PartNumberSpec']")
                except Exception as e2:
                    print(f"Error locating spec table for {part_number}: {e2}")
                    return {"Part Number": part_number, "Error": "Spec table not found"}

    # Get all data rows with multiple approaches
    rows = []
    row_selectors = [
        "tr.PartNumberSpecColumns_dataRow__M4B4a",
        "tr[class*='dataRow']",
        "tbody tr",
        "tr"
    ]
    
    for selector in row_selectors:
        try:
            rows = spec_table.find_elements(By.CSS_SELECTOR, selector)
            if rows:
                print(f"Found {len(rows)} spec rows with selector: {selector}")
                break
        except Exception as e:
            print(f"Row selector {selector} failed: {e}")
            continue

    if not rows:
        print(f"No rows found in spec table for {part_number}")
        return {"Part Number": part_number, "Error": "No rows found"}

    # Define the columns to extract and their mapping to output keys
    columns_map = {
        "Minimum order Qty": "Minimum order Qty",
        "Volumn Discount": "Volumn Discount",
        "Inner Dia. d": "Inner Dia. d",
        "Outer Dia. D": "Outer Dia. D",
        "Width B": "Width B (or T)",
        "Width T": "Width B (or T)",
        "Basic Load Rating Cr (Dynamic)": "Basic Load Rating Cr (Dynamic)",
        "Basic Load Rating Cor (Static)": "Basic Load Rating Cor (Static)",
        "Weight": "Weight"
    }

    # Get header columns to determine index of each field
    header_row = None
    header_cells = []
    header_titles = []
    
    try:
        header_row = spec_table.find_element(By.TAG_NAME, "thead").find_element(By.TAG_NAME, "tr")
        header_cells = header_row.find_elements(By.CSS_SELECTOR, "th.PartNumberSpecCells_dataCell__iK7rr")
        header_titles = [cell.text.strip() for cell in header_cells]
    except Exception as e:
        print(f"Error getting header for {part_number}: {e}")
        # Try alternative header approaches
        try:
            header_cells = spec_table.find_elements(By.CSS_SELECTOR, "th")
            header_titles = [cell.text.strip() for cell in header_cells]
        except:
            try:
                header_cells = spec_table.find_elements(By.CSS_SELECTOR, "[class*='header']")
                header_titles = [cell.text.strip() for cell in header_cells]
            except:
                print(f"Could not get header titles for {part_number}")
                header_titles = []

    # Map header indices to our desired columns
    col_indices = {}
    for idx, title in enumerate(header_titles):
        for key in columns_map:
            if key.lower() in title.lower():
                # For "Width B (or T)", prefer "Width B" but fallback to "Width T"
                if key in ["Width B", "Width T"]:
                    col_indices["Width B (or T)"] = idx
                else:
                    col_indices[columns_map[key]] = idx

    # Prepare spec_data with default values
    spec_data = {
        "Index": index,
        "Part Number": "",
        "Price": "",
        "Days to Ship": "",
        "Minimum order Qty": "",
        "Volumn Discount": "",
        "Inner Dia. d": "",
        "Outer Dia. D": "",
        "Width B (or T)": "",
        "Basic Load Rating Cr (Dynamic)": "",
        "Basic Load Rating Cor (Static)": "",
        "Weight": ""
    }

    # Find the row that matches the part_number
    found_row = None
    for row in rows:
        try:
            tds = row.find_elements(By.CSS_SELECTOR, "td.PartNumberSpecCells_dataCell__iK7rr")
            if not tds:
                # Try alternative cell selectors
                tds = row.find_elements(By.TAG_NAME, "td")
            
            if not tds:
                continue
                
            # The part number is usually in the first cell
            try:
                part_num_div = tds[0].find_element(By.CLASS_NAME, "PartNumberSpecCells_data__u6ZZX")
                row_part_number = part_num_div.text.strip()
            except:
                # Try alternative part number extraction
                row_part_number = tds[0].text.strip()
                
            if row_part_number == part_number:
                found_row = tds
                spec_data["Part Number"] = row_part_number
                break
        except Exception as e:
            print(f"Error matching part number in row: {e}")
            continue

    if found_row:
        # Extract all required columns
        for col_name, idx in col_indices.items():
            try:
                if idx < len(found_row):
                    cell = found_row[idx]
                    try:
                        data_div = cell.find_element(By.CLASS_NAME, "PartNumberSpecCells_data__u6ZZX")
                        value = data_div.text.strip()
                    except:
                        # Try alternative data extraction
                        value = cell.text.strip()
                    spec_data[col_name] = value
                else:
                    spec_data[col_name] = ""
            except Exception as e:
                spec_data[col_name] = ""
        
        # Optionally, extract price and days to ship if present in the columns
        if "Price" in header_titles:
            try:
                price_idx = header_titles.index("Price")
                if price_idx < len(found_row):
                    price_cell = found_row[price_idx]
                    try:
                        price_div = price_cell.find_element(By.CLASS_NAME, "PartNumberSpecCells_data__u6ZZX")
                        spec_data["Price"] = price_div.text.strip()
                    except:
                        spec_data["Price"] = price_cell.text.strip()
            except Exception:
                spec_data["Price"] = ""
                
        if "Days to Ship" in header_titles:
            try:
                dts_idx = header_titles.index("Days to Ship")
                if dts_idx < len(found_row):
                    dts_cell = found_row[dts_idx]
                    try:
                        dts_div = dts_cell.find_element(By.CLASS_NAME, "PartNumberSpecCells_data__u6ZZX")
                        spec_data["Days to Ship"] = dts_div.text.strip()
                    except:
                        spec_data["Days to Ship"] = dts_cell.text.strip()
            except Exception:
                spec_data["Days to Ship"] = ""
    else:
        print(f"Part number {part_number} not found in table.")
        spec_data["Error"] = "Part number not found"

    print("spec_data:", spec_data)
    return spec_data

def debug_page_structure(driver):
    """Debug function to understand the page structure"""
    print("=== DEBUGGING PAGE STRUCTURE ===")
    
    # Check for common elements
    try:
        elements = driver.find_elements(By.XPATH, "//*[@id='codeList']")
        print(f"Found {len(elements)} elements with id 'codeList'")
    except:
        print("No elements with id 'codeList' found")
    
    try:
        elements = driver.find_elements(By.XPATH, "//*[contains(@class,'dropdown')]")
        print(f"Found {len(elements)} elements with 'dropdown' in class")
    except:
        print("No dropdown elements found")
    
    try:
        elements = driver.find_elements(By.XPATH, "//table")
        print(f"Found {len(elements)} table elements")
    except:
        print("No table elements found")
    
    try:
        elements = driver.find_elements(By.XPATH, "//*[contains(@class,'PartNumber')]")
        print(f"Found {len(elements)} elements with 'PartNumber' in class")
    except:
        print("No PartNumber elements found")
    
    # Print page title and URL
    print(f"Page title: {driver.title}")
    print(f"Current URL: {driver.current_url}")
    print("=== END DEBUG ===")

# ====== MAIN ======
def main():
    url = "https://vn.misumi-ec.com/vona2/detail/110310367019/?KWSearch=bearing&searchFlow=results2products&list=PageSearchResult"

    # Khởi tạo Chrome
    driver = setup_driver()
    if not driver:
        print("Failed to setup Chrome driver")
        return
    
    try:
        driver.maximize_window()
        driver.get(url)
        
        # Debug page structure
        debug_page_structure(driver)

        print("Đang lấy danh sách Part Numbers...")
        part_numbers = extract_all_part_numbers(driver)
        
        if not part_numbers:
            print("ERROR: No part numbers found. The page structure may have changed.")
            print("Please check the website manually to see if the structure has changed.")
            return
            
        print(f"Tìm thấy {len(part_numbers)} part numbers.")
        temp_part_numbers = part_numbers
        all_data = []
        
        for idx, pn in enumerate(part_numbers, start=1):
            print(f"({idx}/{len(part_numbers)}) Đang lấy dữ liệu: {pn}")
            try:
                data = get_data_match_part_number(driver, idx, pn)
                data["Part Number"] = temp_part_numbers[idx-1]
                all_data.append(data)
            except Exception as e:
                print(f"Error processing part number {pn}: {e}")
                all_data.append({"Part Number": pn, "Error": str(e)})
            time.sleep(1)
        
        print("all_data:", all_data)
        
        # Save to Excel if data is available
        if all_data:
            try:
                df = pd.DataFrame(all_data)
                output_file = "misumi_bearings.xlsx"
                df.to_excel(output_file, index=False)
                print(f"✅ Đã lưu dữ liệu vào {output_file}")
            except Exception as e:
                print(f"Error saving to Excel: {e}")
        else:
            print("⚠ Không lấy được dữ liệu nào.")
            
    except Exception as e:
        print(f"Error in main function: {e}")
    finally:
        driver.quit()


if __name__ == "__main__":
    main()