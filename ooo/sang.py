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
    chrome_options.add_argument("--disable-blink-features=AutomationControlled")
    chrome_options.add_argument("--disable-dev-shm-usage")
    chrome_options.add_argument("--disable-gpu")
    chrome_options.add_argument("--disable-gpu-sandbox")
    chrome_options.add_argument("--disable-web-security")
    chrome_options.add_argument("--disable-features=VizDisplayCompositor")
    chrome_options.add_argument("--disable-software-rasterizer")
    chrome_options.add_argument("--disable-extensions")
    chrome_options.add_argument("--disable-plugins")
    chrome_options.add_argument("--disable-images")
    chrome_options.add_argument("--disable-javascript")
    chrome_options.add_argument("--window-size=1920,1080")
    chrome_options.add_argument("--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36")
    chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
    chrome_options.add_experimental_option('useAutomationExtension', False)
    chrome_options.add_experimental_option("prefs", {
        "profile.default_content_setting_values": {
            "images": 2,
            "plugins": 2,
            "popups": 2,
            "geolocation": 2,
            "notifications": 2,
            "media_stream": 2,
        }
    })
    try:
        driver = webdriver.Chrome(options=chrome_options)
        driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
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
        (By.CLASS_NAME, "PartNumberColumn_tableBase__DK2Le"),  # Updated class name
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
        "tbody tr.PartNumberColumn_dataRow__DK2Le",  # Updated for new class
        "tbody tr.PartNumberAsideColumns_dataRow__OUw8N",
        "tbody tr",
        "tr.PartNumberColumn_dataRow__DK2Le",  # Updated for new class
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
    for i, row in enumerate(rows[:5]):  # Check first 5 rows
        try:
            cells = row.find_elements(By.TAG_NAME, "td")
            print(f"Row {i} has {len(cells)} cells:")
            for j, cell in enumerate(cells):
                cell_text = cell.text.strip()
                print(f"  Cell {j}: '{cell_text}'")
        except Exception as e:
            print(f"Error debugging row {i}: {e}")
    print("=== END DEBUG ===")
    
    # Look for part numbers in the page source or try to find them in a different way
    print("=== SEARCHING FOR PART NUMBERS ===")
    
    # First, try to find part numbers from dropdown options (most reliable)
    print("=== SEARCHING DROPDOWN OPTIONS ===")
    try:
        # Look for dropdown options that contain part numbers
        dropdown_options = driver.find_elements(By.XPATH, "//div[contains(@class,'PartNumberDropDownList_partNumberOption')]")
        print(f"Found {len(dropdown_options)} dropdown options")
        
        for option in dropdown_options:
            try:
                text = option.text.strip()
                if text and len(text) >= 4 and not any(currency in text for currency in ["VND", "$", "¥", "€", "£"]):
                    if text not in part_numbers:
                        part_numbers.append(text)
                        print(f"Found part number from dropdown: {text}")
            except:
                continue
        
        # If we found part numbers from dropdown, use them
        if part_numbers:
            print(f"Using {len(part_numbers)} part numbers from dropdown options")
            return part_numbers[:60]  # Limit to exactly 60
                
    except Exception as e:
        print(f"Error finding dropdown options: {e}")
    
    # If no part numbers from dropdown, try page source
    if not part_numbers:
        print("=== SEARCHING PAGE SOURCE ===")
        try:
            # Look for part number patterns in the page
            page_source = driver.page_source
            
            # Common bearing part number patterns
            import re
            part_number_patterns = [
                r'\b\d{4}[-_]?[A-Z]{2,3}\b',  # 6200-2RS, 6200ZZ
                r'\b\d{4}[-_]?[A-Z]\d[A-Z]\b',  # 6200-2Z
                r'\b[A-Z]{2,3}\d{4}\b',  # ZZ6200
                r'\b\d{4}[A-Z]{2,3}\b',  # 6200ZZ
            ]
            
            found_part_numbers = []
            for pattern in part_number_patterns:
                matches = re.findall(pattern, page_source)
                found_part_numbers.extend(matches)
            
            # Remove duplicates and filter out obvious non-part-numbers
            unique_part_numbers = []
            for pn in set(found_part_numbers):
                if len(pn) >= 4 and not any(currency in pn for currency in ["VND", "$", "¥", "€", "£"]):
                    unique_part_numbers.append(pn)
            
            print(f"Found {len(unique_part_numbers)} potential part numbers from page source: {unique_part_numbers}")
            
            # Don't return immediately, continue to table extraction
            part_numbers.extend(unique_part_numbers)
                
        except Exception as e:
            print(f"Error searching page source: {e}")
    
    # Now try to extract from table - this should be the main source
    print("=== EXTRACTING FROM TABLE ROWS ===")
    
    for i, row in enumerate(rows):
        try:
            cells = row.find_elements(By.TAG_NAME, "td")
            if not cells:
                continue
            
            # Look for part number in each cell
            for j, cell in enumerate(cells):
                cell_text = cell.text.strip()
                if not cell_text:
                    continue
                
                # Part number validation - must contain both letters and numbers
                if (len(cell_text) >= 4 and 
                    any(char.isdigit() for char in cell_text) and
                    any(char.isalpha() for char in cell_text) and
                    not any(currency in cell_text for currency in ["VND", "$", "¥", "€", "£"]) and
                    not "day" in cell_text.lower() and
                    not "ship" in cell_text.lower() and
                    not "qty" in cell_text.lower() and
                    not "discount" in cell_text.lower() and
                    not cell_text.isdigit()):  # Not just numbers
                    
                    # Additional validation for bearing part numbers
                    if (cell_text.startswith(('6', '7', '8', '9', 'C-E')) or  # Common bearing series including C-E
                        '-' in cell_text or
                        any(suffix in cell_text.upper() for suffix in ['RS', 'ZZ', 'Z', '2RS', '2Z', 'GTM'])):
                        if cell_text not in part_numbers:
                            part_numbers.append(cell_text)
                            print(f"Found part number from table: {cell_text}")
                        break
            
        except Exception as e:
            print(f"Error processing row {i}: {e}")
            continue
    
    # If still no part numbers, try to find them in the page source with broader patterns
    if not part_numbers:
        print("=== SEARCHING PAGE SOURCE WITH BROADER PATTERNS ===")
        try:
            page_source = driver.page_source
            
            # Broader patterns for part numbers
            import re
            broader_patterns = [
                r'\b\d{4}[A-Z]{2,3}\b',  # 6200ZZ, 2520GTM
                r'\b\d{4}[-_]?[A-Z]{2,3}\b',  # 6200-2RS, 6200ZZ
                r'\b[A-Z]{2,3}\d{4}\b',  # ZZ6200
                r'\b\d{4}[A-Z]\d[A-Z]\b',  # 6200-2Z
                r'\b\d{4}[A-Z]{1,4}\b',  # Any 4 digits followed by 1-4 letters
            ]
            
            for pattern in broader_patterns:
                matches = re.findall(pattern, page_source)
                for match in matches:
                    if match not in part_numbers and len(match) >= 4:
                        part_numbers.append(match)
                        print(f"Found part number from source: {match}")
                        
        except Exception as e:
            print(f"Error searching page source: {e}")
    
    print("Final part_numbers:", part_numbers)
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
    wait = WebDriverWait(driver, 30)  # Reduced timeout
    
    # Check if driver is still connected
    try:
        driver.current_url
    except Exception as e:
        print(f"Driver connection lost for {part_number}: {e}")
        return {"Part Number": part_number, "Error": "Driver connection lost"}
    
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

    # Try to find the main part number table (PartNumberColumn_tableBase__DK2Le)
    table = None
    table_selectors = [
        (By.CLASS_NAME, "PartNumberColumn_tableBase__DK2Le"),  # Main part number table
        (By.CLASS_NAME, "PartNumberAsideColumns_table__6fKVE"),  # Alternative table
        (By.XPATH, "//table[contains(@class,'PartNumber')]"),
        (By.CSS_SELECTOR, "[class*='PartNumber']")
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

    # Try to find the table that contains prices and other data
    price_table = None
    price_table_selectors = [
        (By.CLASS_NAME, "PartNumberAsideColumns_table__6fKVE"),  # Price table
        (By.CLASS_NAME, "PartNumberSpecColumns_tableBase__VK5Nd"),  # Spec table
        (By.XPATH, "//table[contains(@class,'Aside')]"),
        (By.XPATH, "//table[contains(@class,'Spec')]"),
        (By.CSS_SELECTOR, "[class*='Aside']"),
        (By.CSS_SELECTOR, "[class*='Spec']")
    ]
    
    for selector_type, selector in price_table_selectors:
        try:
            print(f"Trying price table selector: {selector}")
            price_table = wait.until(EC.presence_of_element_located((selector_type, selector)))
            print(f"Found price table with selector: {selector}")
            break
        except Exception as e:
            print(f"Price table selector {selector} failed: {e}")
            continue

    # Get all rows from the main table
    rows = []
    row_selectors = [
        "tbody tr",
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
        print(f"No rows found in table for {part_number}")
        return {"Part Number": part_number, "Error": "No rows found"}

    # Prepare spec_data with default values
    spec_data = {
        "Index": index,
        "Part Number": part_number,
        "Price": "",
        "Days to Ship": "",
        "Link": "",
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
            # Look for part number in the row
            cells = row.find_elements(By.TAG_NAME, "td")
            if not cells:
                continue
                
            # Check each cell for the part number
            for cell in cells:
                cell_text = cell.text.strip()
                if cell_text == part_number:
                    found_row = row
                    print(f"Found matching row for {part_number}")
                    break
            
            if found_row:
                break
                
        except Exception as e:
            print(f"Error checking row for {part_number}: {e}")
            continue

    if found_row:
        try:
            # Extract data from the found row
            cells = found_row.find_elements(By.TAG_NAME, "td")
            
            # Get link if available
            try:
                link_elements = found_row.find_elements(By.CSS_SELECTOR, "a[class*='Link'], a[class*='link']")
                if link_elements:
                    spec_data["Link"] = link_elements[0].get_attribute("href") or ""
            except:
                pass
            
            # Get price and other data from cells in THIS specific row
            for i, cell in enumerate(cells):
                cell_text = cell.text.strip()
                
                # Look for price (contains VND, $, etc.) in this specific cell
                if any(currency in cell_text for currency in ["VND", "$", "¥", "€", "£"]):
                    spec_data["Price"] = cell_text
                    print(f"Found price for {part_number}: {cell_text}")
                
                # Look for days to ship
                if "day" in cell_text.lower() or "ship" in cell_text.lower():
                    spec_data["Days to Ship"] = cell_text
                
                # Look for quantity
                if "qty" in cell_text.lower() or cell_text.isdigit():
                    spec_data["Minimum order Qty"] = cell_text
                
                # Look for discount
                if "discount" in cell_text.lower():
                    spec_data["Volumn Discount"] = cell_text
            
            # If no price found in the row, try to find it in the price table
            if not spec_data["Price"] and price_table:
                try:
                    # Get rows from price table
                    price_rows = price_table.find_elements(By.CSS_SELECTOR, "tbody tr, tr")
                    print(f"Found {len(price_rows)} rows in price table")
                    
                    # Find the row index of the current part number in the main table
                    part_number_row_index = None
                    for i, row in enumerate(rows):
                        try:
                            cells = row.find_elements(By.TAG_NAME, "td")
                            for cell in cells:
                                cell_text = cell.text.strip()
                                if cell_text == part_number:
                                    part_number_row_index = i
                                    print(f"Part number {part_number} is at row index {i}")
                                    break
                            if part_number_row_index is not None:
                                break
                        except:
                            continue
                    
                    # Get price from the corresponding row in price table
                    if part_number_row_index is not None and part_number_row_index < len(price_rows):
                        try:
                            price_row = price_rows[part_number_row_index]
                            price_cells = price_row.find_elements(By.TAG_NAME, "td")
                            print(f"Checking price row {part_number_row_index} with {len(price_cells)} cells")
                            
                            for price_cell in price_cells:
                                cell_text = price_cell.text.strip()
                                
                                # Look for price
                                if any(currency in cell_text for currency in ["VND", "$", "¥", "€", "£"]):
                                    spec_data["Price"] = cell_text
                                    print(f"Found price for {part_number} from price table row {part_number_row_index}: {cell_text}")
                                    break
                                
                                # Look for other data
                                if "day" in cell_text.lower() or "ship" in cell_text.lower():
                                    spec_data["Days to Ship"] = cell_text
                                elif "qty" in cell_text.lower() or cell_text.isdigit():
                                    spec_data["Minimum order Qty"] = cell_text
                                elif "discount" in cell_text.lower():
                                    spec_data["Volumn Discount"] = cell_text
                        except Exception as e:
                            print(f"Error getting price from row {part_number_row_index}: {e}")
                    
                    # If still no price, try to find it by searching all rows
                    if not spec_data["Price"]:
                        print(f"No price found for {part_number} at row {part_number_row_index}, searching all rows...")
                        for i, price_row in enumerate(price_rows):
                            try:
                                price_cells = price_row.find_elements(By.TAG_NAME, "td")
                                for price_cell in price_cells:
                                    cell_text = price_cell.text.strip()
                                    
                                    # Look for price
                                    if any(currency in cell_text for currency in ["VND", "$", "¥", "€", "£"]):
                                        spec_data["Price"] = cell_text
                                        print(f"Found price for {part_number} from price table row {i}: {cell_text}")
                                        break
                                
                                if spec_data["Price"]:
                                    break
                            except:
                                continue
                except Exception as e:
                    print(f"Error extracting from price table: {e}")
            
            # If still no price found, try to find it in the page
            if not spec_data["Price"]:
                try:
                    # Look for price elements that might be associated with this part number
                    price_elements = driver.find_elements(By.CSS_SELECTOR, "[class*='PartNumberAsideColumns_data__jikjP'], [class*='price'], [class*='Price']")
                    for elem in price_elements:
                        text = elem.text.strip()
                        if text and any(currency in text for currency in ["VND", "$", "¥", "€", "£"]):
                            # Check if this price element is near or associated with our part number
                            try:
                                # Try to find if this price element is in the same row or near the part number
                                parent = elem.find_element(By.XPATH, "./ancestor::tr[contains(., '" + part_number + "')]")
                                spec_data["Price"] = text
                                print(f"Found price for {part_number} from page: {text}")
                                break
                            except:
                                continue
                except:
                    pass
                
        except Exception as e:
            print(f"Error extracting data for {part_number}: {e}")
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
        all_data = []
        
        # Process part numbers in smaller batches to avoid connection issues
        batch_size = 10
        for batch_start in range(0, len(part_numbers), batch_size):
            batch_end = min(batch_start + batch_size, len(part_numbers))
            batch_part_numbers = part_numbers[batch_start:batch_end]
            
            print(f"Processing batch {batch_start//batch_size + 1}: part numbers {batch_start+1}-{batch_end}")
            
            for idx, pn in enumerate(batch_part_numbers, start=batch_start+1):
                print(f"({idx}/{len(part_numbers)}) Đang lấy dữ liệu: {pn}")
                try:
                    data = get_data_match_part_number(driver, idx, pn)
                    data["Part Number"] = pn  # Ensure correct part number
                    all_data.append(data)
                except Exception as e:
                    print(f"Error processing part number {pn}: {e}")
                    all_data.append({"Part Number": pn, "Error": str(e)})
                
                # Small delay between requests
                time.sleep(1)
            
            # Check if driver is still connected after each batch
            try:
                driver.current_url
            except Exception as e:
                print(f"Driver connection lost after batch {batch_start//batch_size + 1}: {e}")
                break
        
        print("all_data:", all_data)
        
        # Save to Excel if data is available
        if all_data:
            try:
                df = pd.DataFrame(all_data)
                import datetime
                timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
                output_file = f"misumi_bearings_{timestamp}.xlsx"
                df.to_excel(output_file, index=False)
                print(f"✅ Đã lưu dữ liệu vào {output_file}")
                print(f"Total records saved: {len(all_data)}")
                
                # Print summary
                successful_records = [d for d in all_data if "Error" not in d or not d["Error"]]
                error_records = [d for d in all_data if "Error" in d and d["Error"]]
                print(f"Successful records: {len(successful_records)}")
                print(f"Error records: {len(error_records)}")
                
            except Exception as e:
                print(f"Error saving to Excel: {e}")
        else:
            print("⚠ Không lấy được dữ liệu nào.")
            
    except Exception as e:
        print(f"Error in main function: {e}")
    finally:
        try:
            driver.quit()
        except:
            pass


if __name__ == "__main__":
    main() 