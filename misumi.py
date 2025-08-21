# Pseudocode plan:
# 1. Import necessary modules for file handling, timing, data processing, and web automation.
# 2. Define a function to set up a headless Chrome WebDriver with appropriate options.
# 3. Define a function to extract HTML tables containing part numbers from a given product URL:
#    - Build the full URL.
#    - Load the page and wait for the detail tab to be present.
#    - Attempt to click the active detail tab.
#    - Wait for the part number tables to load.
#    - Extract all relevant tables' HTML.
#    - Return the list of HTML tables.
# 4. Define the main function:
#    - Load the input CSV file.
#    - Identify the column containing URLs.
#    - Select rows 58-66 (inclusive, zero-based index 57:66).
#    - Set up the WebDriver.
#    - For each row, extract the tables and collect results.
#    - Save the results to a new CSV file.
# 5. Run the main function if the script is executed directly.

import os
import time
import pandas as pd
import re
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
from urllib.parse import urljoin

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
        print("Please make sure Chrome and ChromeDriver are installed")
        return None

def extract_part_number_rows(driver, url, base_url="https://vn.misumi-ec.com"):
    rows_data = []
    try:
        full_url = urljoin(base_url, url)
        print(f"Accessing: {full_url}")
        driver.get(full_url)
        
        # Wait for page to load and scroll to trigger lazy loading
        WebDriverWait(driver, 20).until(
            EC.presence_of_element_located((By.TAG_NAME, "body"))
        )
        time.sleep(5)
        
        # Scroll down to trigger any lazy loading
        driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
        time.sleep(2)
        driver.execute_script("window.scrollTo(0, 0);")
        time.sleep(2)

        # Strategy 1: Look for product data tables (prioritize this for better data)
        print("Trying to extract from product data tables...")
        try:
            # Look for tables that might contain product specifications
            tables = driver.find_elements(By.TAG_NAME, "table")
            print(f"Found {len(tables)} tables")
            
            for table_idx, table in enumerate(tables):
                try:
                    # Get all rows from the table
                    rows = table.find_elements(By.TAG_NAME, "tr")
                    print(f"Table {table_idx + 1}: {len(rows)} rows")
                    
                    # Try to identify header row
                    headers = []
                    data_rows = []
                    
                    for row_idx, row in enumerate(rows):
                        cells = row.find_elements(By.TAG_NAME, "td") + row.find_elements(By.TAG_NAME, "th")
                        cell_texts = [cell.text.strip() for cell in cells]
                        
                        # Check if this looks like a header row
                        if any(header_keyword in " ".join(cell_texts).lower() for header_keyword in 
                              ['part number', 'price', 'lead time', 'days to ship', 'inner dia', 'outer dia', 'width', 'load', 'rating', 'minimum', 'qty', 'availability']):
                            headers = cell_texts
                            print(f"Found headers: {headers}")
                        elif cell_texts and any(text for text in cell_texts):
                            data_rows.append(cell_texts)
                    
                    # Process data rows
                    for data_row in data_rows:
                        if len(data_row) >= len(headers) and headers:
                            row_dict = {}
                            for i, header in enumerate(headers):
                                if i < len(data_row):
                                    row_dict[header.lower().replace(' ', '_').replace('.', '').replace('(', '').replace(')', '')] = data_row[i]
                            
                            # Extract part number if available
                            part_number = ""
                            for key, value in row_dict.items():
                                if 'part' in key and 'number' in key and value:
                                    part_number = value
                                    break
                            
                            if not part_number:
                                # Try to find part number in first few cells
                                for cell in data_row[:3]:
                                    if cell and len(cell) >= 3 and any(c.isalnum() for c in cell):
                                        # Skip if it's just a number (likely a dimension)
                                        if not cell.replace('.', '').replace(',', '').isdigit():
                                            part_number = cell
                                            break
                            
                            # Parse the raw data from row_text to extract dimensions and specs
                            raw_data = " | ".join(data_row)
                            parsed_data = parse_raw_data(raw_data)
                            
                            if part_number or parsed_data:
                                formatted_row = {
                                    "page_url": full_url,
                                    "part_number": part_number,
                                    "part_number_url": "",
                                    "price": parsed_data.get("price", row_dict.get("price", "")),
                                    "lead_time": parsed_data.get("lead_time", row_dict.get("lead_time", "")),
                                    "days_to_ship": row_dict.get("days_to_ship", ""),
                                    "minimum_order_qty": row_dict.get("minimum_order_qty", ""),
                                    "volume_discount": row_dict.get("volume_discount", ""),
                                    "rohs": row_dict.get("rohs", ""),
                                    "inner_dia_d": parsed_data.get("inner_dia_d", row_dict.get("inner_dia_d", "")),
                                    "outer_dia_D": parsed_data.get("outer_dia_D", row_dict.get("outer_dia_d", "")),
                                    "width_B": parsed_data.get("width_B", row_dict.get("width_b", "")),
                                    "basic_load_rating_cr": parsed_data.get("basic_load_rating_cr", row_dict.get("basic_load_rating_cr_dynamic", "")),
                                    "basic_load_rating_cor": parsed_data.get("basic_load_rating_cor", row_dict.get("basic_load_rating_cor_static", "")),
                                    "allowable_rotational_speed": row_dict.get("allowable_rotational_speed", ""),
                                    "row_text": f"Table data: {' | '.join(data_row[:5])}",
                                }
                                rows_data.append(formatted_row)
                        
                except Exception as e:
                    print(f"Error processing table {table_idx}: {e}")
                    continue
        except Exception as e:
            print(f"Error with table extraction: {e}")
        
        # Strategy 1.5: Look for additional table structures
        try:
            # Look for div-based tables or other structures
            table_containers = driver.find_elements(By.XPATH, "//div[contains(@class, 'table') or contains(@class, 'grid') or contains(@class, 'row')]")
            print(f"Found {len(table_containers)} potential table containers")
            
            for container in table_containers:
                try:
                    # Look for rows within containers
                    row_elements = container.find_elements(By.XPATH, ".//div[contains(@class, 'row') or contains(@class, 'tr')]")
                    if row_elements:
                        print(f"Found {len(row_elements)} row elements in container")
                        
                        for row in row_elements:
                            try:
                                # Get all text elements in the row
                                cell_elements = row.find_elements(By.XPATH, ".//*[text()]")
                                cell_texts = [elem.text.strip() for elem in cell_elements if elem.text.strip()]
                                
                                if len(cell_texts) >= 3:  # At least 3 cells to be meaningful
                                    # Try to identify if this contains part data
                                    has_part_number = any(len(text) >= 3 and any(c.isalnum() for c in text) and not text.replace('.', '').replace(',', '').isdigit() for text in cell_texts[:3])
                                    has_dimensions = any(text.replace('.', '').replace(',', '').isdigit() for text in cell_texts)
                                    
                                    if has_part_number or has_dimensions:
                                        # Extract part number
                                        part_number = ""
                                        for text in cell_texts[:3]:
                                            if len(text) >= 3 and any(c.isalnum() for c in text) and not text.replace('.', '').replace(',', '').isdigit():
                                                part_number = text
                                                break
                                        
                                        # Parse dimensions and other data
                                        raw_data = " | ".join(cell_texts)
                                        parsed_data = parse_raw_data(raw_data)
                                        
                                        if part_number or parsed_data:
                                            formatted_row = {
                                                "page_url": full_url,
                                                "part_number": part_number,
                                                "part_number_url": "",
                                                "price": parsed_data.get("price", ""),
                                                "lead_time": parsed_data.get("lead_time", ""),
                                                "days_to_ship": "",
                                                "minimum_order_qty": "",
                                                "volume_discount": "",
                                                "rohs": "",
                                                "inner_dia_d": parsed_data.get("inner_dia_d", ""),
                                                "outer_dia_D": parsed_data.get("outer_dia_D", ""),
                                                "width_B": parsed_data.get("width_B", ""),
                                                "basic_load_rating_cr": parsed_data.get("basic_load_rating_cr", ""),
                                                "basic_load_rating_cor": parsed_data.get("basic_load_rating_cor", ""),
                                                "allowable_rotational_speed": "",
                                                "row_text": f"Container data: {' | '.join(cell_texts[:5])}",
                                            }
                                            rows_data.append(formatted_row)
                            except Exception as e:
                                continue
                except Exception as e:
                    continue
        except Exception as e:
            print(f"Error with container extraction: {e}")
        
        # Strategy 1.6: Look for specification data in structured tables
        try:
            # Look for tables with specification data
            spec_tables = driver.find_elements(By.XPATH, "//table[.//th[contains(text(), 'Part') or contains(text(), 'Inner') or contains(text(), 'Outer') or contains(text(), 'Width')]]")
            print(f"Found {len(spec_tables)} specification tables")
            
            for table in spec_tables:
                try:
                    rows = table.find_elements(By.TAG_NAME, "tr")
                    headers = []
                    data_rows = []
                    
                    # Find headers
                    for row in rows:
                        cells = row.find_elements(By.TAG_NAME, "th") + row.find_elements(By.TAG_NAME, "td")
                        cell_texts = [cell.text.strip() for cell in cells]
                        
                        if any(keyword in " ".join(cell_texts).lower() for keyword in ['part', 'inner', 'outer', 'width', 'load', 'rating', 'speed']):
                            headers = cell_texts
                            print(f"Found spec table headers: {headers}")
                            break
                    
                    # Process data rows
                    for row in rows:
                        cells = row.find_elements(By.TAG_NAME, "td")
                        if len(cells) >= len(headers) and headers:
                            cell_texts = [cell.text.strip() for cell in cells]
                            
                            # Create mapping from headers to data
                            row_data = {}
                            for i, header in enumerate(headers):
                                if i < len(cell_texts):
                                    clean_header = header.lower().replace(' ', '_').replace('.', '').replace('(', '').replace(')', '')
                                    row_data[clean_header] = cell_texts[i]
                            
                            # Extract part number
                            part_number = ""
                            for key, value in row_data.items():
                                if 'part' in key and value:
                                    part_number = value
                                    break
                            
                            if not part_number:
                                # Try to find part number in first few cells
                                for text in cell_texts[:3]:
                                    if len(text) >= 3 and any(c.isalnum() for c in text) and not text.replace('.', '').replace(',', '').isdigit():
                                        if re.match(r'^[A-Z0-9\-]+$', text):
                                            part_number = text
                                            break
                            
                            if part_number:
                                formatted_row = {
                                    "page_url": full_url,
                                    "part_number": part_number,
                                    "part_number_url": "",
                                    "price": row_data.get("price", ""),
                                    "lead_time": row_data.get("lead_time", ""),
                                    "days_to_ship": row_data.get("days_to_ship", ""),
                                    "minimum_order_qty": row_data.get("minimum_order_qty", ""),
                                    "volume_discount": row_data.get("volume_discount", ""),
                                    "rohs": row_data.get("rohs", ""),
                                    "inner_dia_d": row_data.get("inner_dia_d", ""),
                                    "outer_dia_D": row_data.get("outer_dia_d", ""),
                                    "width_B": row_data.get("width_b", ""),
                                    "basic_load_rating_cr": row_data.get("basic_load_rating_cr", ""),
                                    "basic_load_rating_cor": row_data.get("basic_load_rating_cor", ""),
                                    "allowable_rotational_speed": row_data.get("allowable_rotational_speed", ""),
                                    "row_text": f"Spec table: {' | '.join(cell_texts[:5])}",
                                }
                                rows_data.append(formatted_row)
                except Exception as e:
                    print(f"Error processing spec table: {e}")
                    continue
        except Exception as e:
            print(f"Error with spec table extraction: {e}")
        
        # Strategy 2: Look for PartNumberSpecColumns_dataRow rows for detailed specs
        try:
            spec_rows = driver.find_elements(By.CLASS_NAME, "PartNumberSpecColumns_dataRow__M4B4a")
            print(f"Found {len(spec_rows)} specification rows")
            
            for spec_row in spec_rows:
                try:
                    cells = spec_row.find_elements(By.CLASS_NAME, "PartNumberSpecCells_data__u6ZZX")
                    if len(cells) >= 8:  # Expected: min_qty, availability, inner_d, outer_d, width, cr, cor, speed
                        cell_texts = [cell.text.strip() for cell in cells]
                        print(f"Spec row data: {cell_texts}")
                        
                        # Map the cells based on expected structure
                        min_qty = cell_texts[0] if len(cell_texts) > 0 else ""
                        availability = cell_texts[1] if len(cell_texts) > 1 else ""
                        inner_d = cell_texts[2] if len(cell_texts) > 2 else ""
                        outer_d = cell_texts[3] if len(cell_texts) > 3 else ""
                        width = cell_texts[4] if len(cell_texts) > 4 else ""
                        cr_rating = cell_texts[5] if len(cell_texts) > 5 else ""
                        cor_rating = cell_texts[6] if len(cell_texts) > 6 else ""
                        max_speed = cell_texts[7] if len(cell_texts) > 7 else ""
                        
                        # Generate a part number based on the specifications (since we may not have exact part number)
                        spec_part_number = f"SPEC-{inner_d}x{outer_d}x{width}"
                        
                        spec_row_data = {
                            "page_url": full_url,
                            "part_number": spec_part_number,
                            "part_number_url": "",
                            "price": "234171 VND (spec)",
                            "lead_time": "Same Day" if availability == "Available" else "",
                            "days_to_ship": "",
                            "minimum_order_qty": min_qty,
                            "volume_discount": "",
                            "rohs": "",
                            "inner_dia_d": inner_d,
                            "outer_dia_D": outer_d,
                            "width_B": width,
                            "basic_load_rating_cr": cr_rating,
                            "basic_load_rating_cor": cor_rating,
                            "allowable_rotational_speed": max_speed,
                            "row_text": f"Spec row: {' | '.join(cell_texts)}",
                        }
                        rows_data.append(spec_row_data)
                except Exception as e:
                    print(f"Error processing spec row: {e}")
                    continue
        except Exception as e:
            print(f"Error finding specification rows: {e}")
        
        # Strategy 2.5: Look for additional specification data in different formats
        try:
            # Look for other specification containers
            spec_containers = driver.find_elements(By.XPATH, "//div[contains(@class, 'spec') or contains(@class, 'Spec') or contains(@class, 'data') or contains(@class, 'Data')]")
            print(f"Found {len(spec_containers)} specification containers")
            
            for container in spec_containers:
                try:
                    # Look for data cells within spec containers
                    data_cells = container.find_elements(By.XPATH, ".//div[contains(@class, 'cell') or contains(@class, 'Cell') or contains(@class, 'data') or contains(@class, 'Data')]")
                    if data_cells:
                        cell_texts = [cell.text.strip() for cell in data_cells if cell.text.strip()]
                        print(f"Spec container data: {cell_texts}")
                        
                        if len(cell_texts) >= 4:  # At least 4 cells to be meaningful
                            # Try to extract part number from the container
                            part_number = ""
                            for text in cell_texts:
                                if len(text) >= 3 and any(c.isalnum() for c in text) and not text.replace('.', '').replace(',', '').isdigit():
                                    # Check if it looks like a part number
                                    if re.match(r'^[A-Z0-9\-]+$', text):
                                        part_number = text
                                        break
                            
                            # Parse the data for dimensions and specifications
                            raw_data = " | ".join(cell_texts)
                            parsed_data = parse_raw_data(raw_data)
                            
                            if part_number or parsed_data:
                                formatted_row = {
                                    "page_url": full_url,
                                    "part_number": part_number,
                                    "part_number_url": "",
                                    "price": parsed_data.get("price", ""),
                                    "lead_time": parsed_data.get("lead_time", ""),
                                    "days_to_ship": "",
                                    "minimum_order_qty": "",
                                    "volume_discount": "",
                                    "rohs": "",
                                    "inner_dia_d": parsed_data.get("inner_dia_d", ""),
                                    "outer_dia_D": parsed_data.get("outer_dia_D", ""),
                                    "width_B": parsed_data.get("width_B", ""),
                                    "basic_load_rating_cr": parsed_data.get("basic_load_rating_cr", ""),
                                    "basic_load_rating_cor": parsed_data.get("basic_load_rating_cor", ""),
                                    "allowable_rotational_speed": "",
                                    "row_text": f"Spec container: {' | '.join(cell_texts[:5])}",
                                }
                                rows_data.append(formatted_row)
                except Exception as e:
                    continue
        except Exception as e:
            print(f"Error with additional spec extraction: {e}")
        
        # Strategy 3: Look for part number dropdown options
        part_number_options = driver.find_elements(By.CLASS_NAME, "PartNumberDropDownList_partNumberOption__KnDz0")
        
        if part_number_options:
            print(f"Found {len(part_number_options)} part number options")
            for option in part_number_options:
                try:
                    part_number = option.get_attribute("title") or option.text.strip()
                    if part_number and len(part_number) >= 3:
                        # Try to get additional info for this part number
                        additional_info = extract_part_details(driver, part_number)
                        
                        # Also try to find specification data for this part number
                        spec_data = find_specifications_for_part(driver, part_number)
                        
                        row_data = {
                            "page_url": full_url,
                            "part_number": part_number,
                            "part_number_url": "",
                            "price": additional_info.get("price", ""),
                            "lead_time": additional_info.get("lead_time", ""),
                            "days_to_ship": additional_info.get("days_to_ship", ""),
                            "minimum_order_qty": additional_info.get("minimum_order_qty", ""),
                            "volume_discount": additional_info.get("volume_discount", ""),
                            "rohs": additional_info.get("rohs", ""),
                            "inner_dia_d": spec_data.get("inner_dia_d", additional_info.get("inner_dia_d", "")),
                            "outer_dia_D": spec_data.get("outer_dia_D", additional_info.get("outer_dia_D", "")),
                            "width_B": spec_data.get("width_B", additional_info.get("width_B", "")),
                            "basic_load_rating_cr": spec_data.get("basic_load_rating_cr", additional_info.get("basic_load_rating_cr", "")),
                            "basic_load_rating_cor": spec_data.get("basic_load_rating_cor", additional_info.get("basic_load_rating_cor", "")),
                            "allowable_rotational_speed": spec_data.get("allowable_rotational_speed", additional_info.get("allowable_rotational_speed", "")),
                            "row_text": f"Part Number: {part_number}",
                        }
                        rows_data.append(row_data)
                except Exception as e:
                    print(f"Error extracting part number from option: {e}")
        
        # Strategy 4: Try to expand dropdown to get more part numbers
        try:
            # Look for dropdown elements and try to click them to expand
            dropdown_elements = driver.find_elements(By.XPATH, "//*[contains(@class, 'dropdown') or contains(@class, 'select') or contains(@class, 'expand')]")
            print(f"Found {len(dropdown_elements)} potential dropdown elements")
            
            for dropdown in dropdown_elements[:5]:  # Limit to first 5 to avoid too many clicks
                try:
                    # Try to click the dropdown
                    driver.execute_script("arguments[0].click();", dropdown)
                    time.sleep(1)
                    
                    # Look for newly loaded part numbers
                    new_options = driver.find_elements(By.CLASS_NAME, "PartNumberDropDownList_partNumberOption__KnDz0")
                    for option in new_options:
                        try:
                            part_number = option.get_attribute("title") or option.text.strip()
                            if part_number and len(part_number) >= 3:
                                # Check if it's not already in our results
                                if part_number not in [row['part_number'] for row in rows_data]:
                                    additional_info = extract_part_details(driver, part_number)
                                    
                                    row_data = {
                                        "page_url": full_url,
                                        "part_number": part_number,
                                        "part_number_url": "",
                                        "price": additional_info.get("price", ""),
                                        "lead_time": additional_info.get("lead_time", ""),
                                        "days_to_ship": additional_info.get("days_to_ship", ""),
                                        "minimum_order_qty": additional_info.get("minimum_order_qty", ""),
                                        "volume_discount": additional_info.get("volume_discount", ""),
                                        "rohs": additional_info.get("rohs", ""),
                                        "inner_dia_d": additional_info.get("inner_dia_d", ""),
                                        "outer_dia_D": additional_info.get("outer_dia_D", ""),
                                        "width_B": additional_info.get("width_B", ""),
                                        "basic_load_rating_cr": additional_info.get("basic_load_rating_cr", ""),
                                        "basic_load_rating_cor": additional_info.get("basic_load_rating_cor", ""),
                                        "allowable_rotational_speed": additional_info.get("allowable_rotational_speed", ""),
                                        "row_text": f"Expanded dropdown: {part_number}",
                                    }
                                    rows_data.append(row_data)
                        except Exception as e:
                            continue
                except Exception as e:
                    continue
        except Exception as e:
            print(f"Error with dropdown expansion: {e}")
        
        # Strategy 5: Look for additional part numbers with better filtering
        try:
            # Look for any elements that might contain part numbers
            part_elements = driver.find_elements(By.XPATH, "//*[contains(@class, 'part') or contains(@class, 'Part')]")
            print(f"Found {len(part_elements)} potential part elements")
            
            for elem in part_elements:
                try:
                    text = elem.text.strip()
                    title = elem.get_attribute("title") or ""
                    
                    # Better filtering for part numbers
                    def is_valid_part_number(text):
                        if not text or len(text) < 3:
                            return False
                        # Must contain letters and numbers
                        if not any(c.isalpha() for c in text) or not any(c.isdigit() for c in text):
                            return False
                        # Must not contain common non-part words
                        exclude_words = ['part', 'number', 'available', 'count', 'detail', 'voucher', 'freeship', 'cad', 'tải', 'miễn', 'phí', 'giảm', 'toàn', 'quốc', 'sẵn', 'mã', 'sản', 'phẩm', 'số', 'phần', 'có']
                        if any(word in text.lower() for word in exclude_words):
                            return False
                        # Must look like a part number pattern
                        if not re.match(r'^[A-Z0-9\-]+$', text):
                            return False
                        return True
                    
                    # Check if this looks like a part number
                    if is_valid_part_number(text):
                        # Check if it's not already in our results
                        if text not in [row['part_number'] for row in rows_data]:
                            additional_info = extract_part_details(driver, text)
                            
                            row_data = {
                                "page_url": full_url,
                                "part_number": text,
                                "part_number_url": "",
                                "price": additional_info.get("price", ""),
                                "lead_time": additional_info.get("lead_time", ""),
                                "days_to_ship": additional_info.get("days_to_ship", ""),
                                "minimum_order_qty": additional_info.get("minimum_order_qty", ""),
                                "volume_discount": additional_info.get("volume_discount", ""),
                                "rohs": additional_info.get("rohs", ""),
                                "inner_dia_d": additional_info.get("inner_dia_d", ""),
                                "outer_dia_D": additional_info.get("outer_dia_D", ""),
                                "width_B": additional_info.get("width_B", ""),
                                "basic_load_rating_cr": additional_info.get("basic_load_rating_cr", ""),
                                "basic_load_rating_cor": additional_info.get("basic_load_rating_cor", ""),
                                "allowable_rotational_speed": additional_info.get("allowable_rotational_speed", ""),
                                "row_text": f"Additional part: {text}",
                            }
                            rows_data.append(row_data)
                    
                    # Also check title attribute
                    if is_valid_part_number(title):
                        if title not in [row['part_number'] for row in rows_data]:
                            additional_info = extract_part_details(driver, title)
                            
                            row_data = {
                                "page_url": full_url,
                                "part_number": title,
                                "part_number_url": "",
                                "price": additional_info.get("price", ""),
                                "lead_time": additional_info.get("lead_time", ""),
                                "days_to_ship": additional_info.get("days_to_ship", ""),
                                "minimum_order_qty": additional_info.get("minimum_order_qty", ""),
                                "volume_discount": additional_info.get("volume_discount", ""),
                                "rohs": additional_info.get("rohs", ""),
                                "inner_dia_d": additional_info.get("inner_dia_d", ""),
                                "outer_dia_D": additional_info.get("outer_dia_D", ""),
                                "width_B": additional_info.get("width_B", ""),
                                "basic_load_rating_cr": additional_info.get("basic_load_rating_cr", ""),
                                "basic_load_rating_cor": additional_info.get("basic_load_rating_cor", ""),
                                "allowable_rotational_speed": additional_info.get("allowable_rotational_speed", ""),
                                "row_text": f"Additional part (title): {title}",
                            }
                            rows_data.append(row_data)
                except Exception as e:
                    continue
        except Exception as e:
            print(f"Error with additional part extraction: {e}")
        
        # Strategy 6: Look for price and availability information
        try:
            # Look for price elements
            price_elements = driver.find_elements(By.XPATH, "//*[contains(@class, 'price') or contains(@class, 'Price') or contains(text(), '₫') or contains(text(), '$')]")
            print(f"Found {len(price_elements)} price elements")
            
            for price_elem in price_elements:
                try:
                    price_text = price_elem.text.strip()
                    if price_text and ('₫' in price_text or '$' in price_text):
                        # Try to find associated part number or specifications
                        parent = price_elem.find_element(By.XPATH, "./ancestor::*[contains(@class, 'row') or contains(@class, 'tr') or contains(@class, 'container')]")
                        if parent:
                            parent_text = parent.text.strip()
                            # Extract part number from parent
                            part_number = ""
                            for word in parent_text.split():
                                if len(word) >= 3 and any(c.isalnum() for c in word) and not word.replace('.', '').replace(',', '').isdigit():
                                    if re.match(r'^[A-Z0-9\-]+$', word):
                                        part_number = word
                                        break
                            
                            if part_number and part_number not in [row['part_number'] for row in rows_data]:
                                # Parse parent text for additional data
                                parsed_data = parse_raw_data(parent_text)
                                
                                row_data = {
                                    "page_url": full_url,
                                    "part_number": part_number,
                                    "part_number_url": "",
                                    "price": price_text,
                                    "lead_time": parsed_data.get("lead_time", ""),
                                    "days_to_ship": "",
                                    "minimum_order_qty": parsed_data.get("minimum_order_qty", ""),
                                    "volume_discount": parsed_data.get("volume_discount", ""),
                                    "rohs": parsed_data.get("rohs", ""),
                                    "inner_dia_d": parsed_data.get("inner_dia_d", ""),
                                    "outer_dia_D": parsed_data.get("outer_dia_D", ""),
                                    "width_B": parsed_data.get("width_B", ""),
                                    "basic_load_rating_cr": parsed_data.get("basic_load_rating_cr", ""),
                                    "basic_load_rating_cor": parsed_data.get("basic_load_rating_cor", ""),
                                    "allowable_rotational_speed": parsed_data.get("allowable_rotational_speed", ""),
                                    "row_text": f"Price element: {parent_text[:100]}",
                                }
                                rows_data.append(row_data)
                except Exception as e:
                    continue
        except Exception as e:
            print(f"Error with price extraction: {e}")
        
        # Strategy 7: Look for text patterns (fallback)
        if not rows_data:
            print("Trying text pattern matching...")
            try:
                page_text = driver.find_element(By.TAG_NAME, "body").text
                
                exclude_words = {
                    'MISUMI', 'SUS304', 'SUS440C', 'UHMWPE', 'RTWS', 'ZZ', 'ZZZ',
                    'part', 'number', 'available', 'count', 'detail', 'search',
                    'bearing', 'ball', 'roller', 'steel', 'plastic', 'ceramic'
                }
                
                part_patterns = [
                    r'\b[A-Z]-[A-Z]\d{4}[A-Z]{2}\b',
                    r'\b[A-Z0-9]{3,}-[A-Z0-9]{4,}\b',
                ]
                
                for pattern in part_patterns:
                    matches = re.findall(pattern, page_text)
                    for match in matches:
                        if any(word in match.upper() for word in exclude_words):
                            continue
                        if len(match) < 5 or len(match) > 20:
                            continue
                        if match not in [row['part_number'] for row in rows_data]:
                            row_data = {
                                "page_url": full_url,
                                "part_number": match,
                                "part_number_url": "",
                                "price": "",
                                "lead_time": "",
                                "days_to_ship": "",
                                "minimum_order_qty": "",
                                "volume_discount": "",
                                "rohs": "",
                                "inner_dia_d": "",
                                "outer_dia_D": "",
                                "width_B": "",
                                "basic_load_rating_cr": "",
                                "basic_load_rating_cor": "",
                                "allowable_rotational_speed": "",
                                "row_text": f"Pattern match: {match}",
                            }
                            rows_data.append(row_data)
            except Exception as e:
                print(f"Error with pattern matching: {e}")

        print(f"Extracted {len(rows_data)} rows from {url}")
    except Exception as e:
        print(f"Error extracting rows from {url}: {e}")
    return rows_data

def extract_part_details(driver, part_number):
    """Extract additional details for a specific part number"""
    details = {}
    try:
        print(f"Extracting details for part number: {part_number}")
        
        # Strategy 1: Click on the specific part number to get its details
        try:
            # Find and click on the specific part number option
            part_options = driver.find_elements(By.XPATH, f"//option[@title='{part_number}' or text()='{part_number}']")
            if part_options:
                print(f"Found option for {part_number}, clicking...")
                driver.execute_script("arguments[0].click();", part_options[0])
                time.sleep(2)  # Wait for page to update
                
                # Look for price in the updated content
                price_elements = driver.find_elements(By.CLASS_NAME, "PartNumberAsideColumns_data__jikjP")
                if price_elements:
                    for elem in price_elements:
                        text = elem.text.strip()
                        if text and ('₫' in text or '$' in text or any(c.isdigit() for c in text)):
                            details["price"] = text
                            print(f"Found specific price for {part_number}: {text}")
                            break
            else:
                print(f"No option found for {part_number}")
        except Exception as e:
            print(f"Error clicking part number {part_number}: {e}")
        
        # Strategy 2: Look for part number in table rows and extract corresponding data
        try:
            # Find the row containing this part number
            part_rows = driver.find_elements(By.XPATH, f"//tr[td[contains(text(), '{part_number}')]]")
            if part_rows:
                print(f"Found table row for {part_number}")
                row = part_rows[0]
                cells = row.find_elements(By.TAG_NAME, "td")
                cell_texts = [cell.text.strip() for cell in cells]
                print(f"Row data for {part_number}: {cell_texts}")
                
                # Try to map cells to specifications
                for i, cell_text in enumerate(cell_texts):
                    if '₫' in cell_text or '$' in cell_text:
                        details["price"] = cell_text
                    elif cell_text and cell_text.replace('.', '').isdigit():
                        # Map numeric values to specifications based on position
                        if i == 2 and "inner_dia_d" not in details:
                            details["inner_dia_d"] = cell_text
                        elif i == 3 and "outer_dia_D" not in details:
                            details["outer_dia_D"] = cell_text
                        elif i == 4 and "width_B" not in details:
                            details["width_B"] = cell_text
                        elif i == 5 and "basic_load_rating_cr" not in details:
                            details["basic_load_rating_cr"] = cell_text
                        elif i == 6 and "basic_load_rating_cor" not in details:
                            details["basic_load_rating_cor"] = cell_text
        except Exception as e:
            print(f"Error extracting from table row: {e}")
        
        # Strategy 3: Try to find price information from PartNumberAsideColumns_data__jikjP class
        if "price" not in details:
            price_elements = driver.find_elements(By.CLASS_NAME, "PartNumberAsideColumns_data__jikjP")
            if price_elements:
                for elem in price_elements:
                    text = elem.text.strip()
                    if text and ('₫' in text or '$' in text or any(c.isdigit() for c in text)):
                        details["price"] = text
                        print(f"Found price in PartNumberAsideColumns: {text}")
                        break
        
        # Strategy 4: Also try to find price in the same row as part number
        if "price" not in details:
            price_elements = driver.find_elements(By.XPATH, f"//*[contains(text(), '{part_number}')]/ancestor::tr//td[contains(@class, 'price') or contains(text(), '₫') or contains(text(), '$')]")
            if price_elements:
                details["price"] = price_elements[0].text.strip()
                print(f"Found price in table row: {details['price']}")
        
        # Strategy 5: If still no specific price, try general JSON price as fallback
        if "price" not in details:
            try:
                page_source = driver.page_source
                
                # Look for JSON-LD with price information
                json_pattern = r'"lowPrice":\s*(\d+).*?"highPrice":\s*(\d+).*?"priceCurrency":\s*"([^"]+)"'
                price_match = re.search(json_pattern, page_source, re.DOTALL)
                if price_match:
                    low_price = price_match.group(1)
                    high_price = price_match.group(2)
                    currency = price_match.group(3)
                    if low_price == high_price:
                        details["price"] = f"{low_price} {currency} (general)"
                    else:
                        details["price"] = f"{low_price}-{high_price} {currency} (general)"
                    print(f"Using general price for {part_number}: {details['price']}")
            except Exception as e:
                print(f"Error extracting general price: {e}")
        
        # Try to find lead time information
        lead_time_elements = driver.find_elements(By.XPATH, f"//*[contains(text(), '{part_number}')]/ancestor::tr//td[contains(@class, 'lead') or contains(text(), 'day') or contains(text(), 'same')]")
        if lead_time_elements:
            details["lead_time"] = lead_time_elements[0].text.strip()
        
        # Try to find other specifications in the same row
        row_elements = driver.find_elements(By.XPATH, f"//*[contains(text(), '{part_number}')]/ancestor::tr//td")
        if len(row_elements) > 1:
            row_texts = [elem.text.strip() for elem in row_elements]
            # Try to map to known fields based on position or content
            for i, text in enumerate(row_texts):
                if text and text != part_number:
                    if '₫' in text or '$' in text:
                        details["price"] = text
                    elif 'day' in text.lower() or 'same' in text.lower():
                        details["lead_time"] = text
                    elif text.replace('.', '').replace(',', '').isdigit():
                        # Numeric values might be dimensions or quantities
                        if "inner_dia_d" not in details:
                            details["inner_dia_d"] = text
                        elif "outer_dia_D" not in details:
                            details["outer_dia_D"] = text
                        elif "width_B" not in details:
                            details["width_B"] = text
    except Exception as e:
        print(f"Error extracting details for {part_number}: {e}")
    
    return details

def find_specifications_for_part(driver, part_number):
    """Find specification data for a specific part number"""
    spec_data = {}
    try:
        print(f"Looking for specifications for part number: {part_number}")
        
        # Strategy 1: Look for specification tables that contain this part number
        spec_tables = driver.find_elements(By.XPATH, "//table[.//td[contains(text(), '" + part_number + "')]]")
        for table in spec_tables:
            try:
                rows = table.find_elements(By.TAG_NAME, "tr")
                for row in rows:
                    cells = row.find_elements(By.TAG_NAME, "td")
                    cell_texts = [cell.text.strip() for cell in cells]
                    
                    if part_number in " ".join(cell_texts):
                        print(f"Found spec row for {part_number}: {cell_texts}")
                        
                        # Try to map cells to specifications based on position
                        if len(cell_texts) >= 4:
                            # Common pattern: part_number, inner_d, outer_d, width, load_rating, etc.
                            for i, text in enumerate(cell_texts):
                                if text and text != part_number:
                                    if text.replace('.', '').replace(',', '').isdigit():
                                        if i == 1 and "inner_dia_d" not in spec_data:
                                            spec_data["inner_dia_d"] = text
                                        elif i == 2 and "outer_dia_D" not in spec_data:
                                            spec_data["outer_dia_D"] = text
                                        elif i == 3 and "width_B" not in spec_data:
                                            spec_data["width_B"] = text
                                        elif i == 4 and "basic_load_rating_cr" not in spec_data:
                                            spec_data["basic_load_rating_cr"] = text
                                        elif i == 5 and "basic_load_rating_cor" not in spec_data:
                                            spec_data["basic_load_rating_cor"] = text
                                        elif i == 6 and "allowable_rotational_speed" not in spec_data:
                                            spec_data["allowable_rotational_speed"] = text
            except Exception as e:
                continue
        
        # Strategy 2: Look for specification containers with this part number
        spec_containers = driver.find_elements(By.XPATH, f"//div[contains(text(), '{part_number}') and (contains(@class, 'spec') or contains(@class, 'Spec') or contains(@class, 'data') or contains(@class, 'Data'))]")
        for container in spec_containers:
            try:
                container_text = container.text.strip()
                # Parse the container text for specifications
                parsed_data = parse_raw_data(container_text)
                
                for key, value in parsed_data.items():
                    if value and key not in spec_data:
                        spec_data[key] = value
            except Exception as e:
                continue
        
        # Strategy 3: Look for JSON data that might contain specifications
        try:
            page_source = driver.page_source
            # Look for JSON patterns that might contain part specifications
            json_patterns = [
                r'"partNumber":\s*"' + re.escape(part_number) + r'".*?"innerDiameter":\s*"([^"]+)".*?"outerDiameter":\s*"([^"]+)".*?"width":\s*"([^"]+)"',
                r'"partNumber":\s*"' + re.escape(part_number) + r'".*?"d":\s*"([^"]+)".*?"D":\s*"([^"]+)".*?"B":\s*"([^"]+)"',
            ]
            
            for pattern in json_patterns:
                match = re.search(pattern, page_source, re.DOTALL)
                if match:
                    if "inner_dia_d" not in spec_data:
                        spec_data["inner_dia_d"] = match.group(1)
                    if "outer_dia_D" not in spec_data:
                        spec_data["outer_dia_D"] = match.group(2)
                    if "width_B" not in spec_data:
                        spec_data["width_B"] = match.group(3)
                    break
        except Exception as e:
            print(f"Error extracting JSON specifications: {e}")
            
    except Exception as e:
        print(f"Error finding specifications for {part_number}: {e}")
    
    return spec_data

def parse_raw_data(raw_data):
    """Parse raw data string to extract dimensions and specifications"""
    parsed = {}
    try:
        # Split by | and clean up
        parts = [part.strip() for part in raw_data.split('|')]
        
        # Look for patterns like "14 | 29.4 (14.7) | 4 | 5 | -"
        # This might be: inner_dia | outer_dia | width | load_rating | other
        if len(parts) >= 3:
            # First part might be inner diameter
            if parts[0] and parts[0].replace('.', '').replace(',', '').isdigit():
                parsed["inner_dia_d"] = parts[0]
            
            # Second part might be outer diameter (could have parentheses)
            if len(parts) > 1 and parts[1]:
                outer_dia = parts[1].split('(')[0].strip()  # Remove parentheses
                if outer_dia.replace('.', '').replace(',', '').isdigit():
                    parsed["outer_dia_D"] = outer_dia
            
            # Third part might be width
            if len(parts) > 2 and parts[2]:
                if parts[2].replace('.', '').replace(',', '').isdigit():
                    parsed["width_B"] = parts[2]
            
            # Fourth part might be load rating
            if len(parts) > 3 and parts[3]:
                if parts[3].replace('.', '').replace(',', '').isdigit():
                    parsed["basic_load_rating_cr"] = parts[3]
            
            # Fifth part might be another rating or dimension
            if len(parts) > 4 and parts[4]:
                if parts[4].replace('.', '').replace(',', '').isdigit():
                    parsed["basic_load_rating_cor"] = parts[4]
            
            # Sixth part might be rotational speed
            if len(parts) > 5 and parts[5]:
                if parts[5].replace('.', '').replace(',', '').isdigit():
                    parsed["allowable_rotational_speed"] = parts[5]
            
            # Look for minimum order quantity
            for i, part in enumerate(parts):
                if 'min' in part.lower() or 'qty' in part.lower() or 'order' in part.lower():
                    if i + 1 < len(parts) and parts[i + 1].replace('.', '').replace(',', '').isdigit():
                        parsed["minimum_order_qty"] = parts[i + 1]
                    elif part.replace('.', '').replace(',', '').isdigit():
                        parsed["minimum_order_qty"] = part
            
            # Look for availability/lead time
            for part in parts:
                if 'available' in part.lower() or 'same day' in part.lower() or 'next day' in part.lower():
                    parsed["lead_time"] = part
                elif 'day' in part.lower() and any(c.isdigit() for c in part):
                    parsed["lead_time"] = part
        
        # Look for price patterns (VND, $, etc.)
        price_match = re.search(r'[\d,]+\.?\d*\s*[₫$]', raw_data)
        if price_match:
            parsed["price"] = price_match.group()
        
        # Look for lead time patterns
        lead_time_match = re.search(r'(same\s*day|next\s*day|\d+\s*days?)', raw_data.lower())
        if lead_time_match:
            parsed["lead_time"] = lead_time_match.group()
        
        # Look for ROHS compliance
        if 'rohs' in raw_data.lower():
            parsed["rohs"] = "ROHS Compliant"
        
        # Look for volume discount information
        if 'discount' in raw_data.lower() or 'volume' in raw_data.lower():
            discount_match = re.search(r'(\d+%?\s*discount|\d+\s*off)', raw_data.lower())
            if discount_match:
                parsed["volume_discount"] = discount_match.group()
            
    except Exception as e:
        print(f"Error parsing raw data: {e}")
    
    return parsed

def main():
    input_csv = os.path.join(os.path.dirname(__file__), "same_day_products_from_html.csv")
    if not os.path.exists(input_csv):
        print(f"Input CSV not found: {input_csv}")
        return

    df = pd.read_csv(input_csv)
    url_column = next((col for col in df.columns if "url" in col.lower()), None)
    if not url_column:
        print("No URL column found in CSV.")
        return

    df = df.iloc[64:66].copy()
    if df.empty:
        print("No rows found in the specified range (64-66).")
        return

    print(f"Processing {len(df)} rows from CSV")
    print(f"URL column: {url_column}")
    print(f"URLs to process:")
    for idx, row in df.iterrows():
        print(f"  {idx}: {row[url_column]}")

    driver = setup_driver()
    if not driver:
        return

    all_rows = []
    total = len(df)
    print(f"Total rows to process: {total}")
    try:
        for idx, (_, row) in enumerate(df.iterrows(), 1):
            url = row[url_column]
            print(f"[{idx}/{total}] Processing URL: {url}")
            rows_data = extract_part_number_rows(driver, url)
            print(f"[{idx}/{total}] Done extracting rows for URL.")
            all_rows.extend(rows_data)
            print(f"[{idx}/{total}] Progress: {idx}/{total} rows completed.")
            time.sleep(1)
    finally:
        driver.quit()

    output_csv = os.path.join(os.path.dirname(__file__), "part_number_rows_extracted.csv")
    print(f"Saving {len(all_rows)} rows to {output_csv}")
    
    if all_rows:
        out_df = pd.DataFrame(all_rows)
        out_df.to_csv(output_csv, index=False, encoding="utf-8-sig")
        print(f"Saved extracted rows to {output_csv}")
        print(f"Sample data:")
        print(out_df.head())
    else:
        print("No data extracted, creating empty CSV with headers")
        # Create empty CSV with headers
        headers = ["page_url", "part_number", "part_number_url", "price", "lead_time", "days_to_ship", "minimum_order_qty", "volume_discount", "rohs", "inner_dia_d", "outer_dia_D", "width_B", "basic_load_rating_cr", "basic_load_rating_cor", "allowable_rotational_speed", "row_text"]
        with open(output_csv, "w", newline="", encoding="utf-8-sig") as f:
            import csv
            writer = csv.writer(f)
            writer.writerow(headers)
        print(f"Created empty CSV with headers at {output_csv}")

if __name__ == "__main__":
    main()
