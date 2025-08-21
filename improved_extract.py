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

def extract_row_data(row_elements, headers, url):
    """Extract data from a single table row"""
    row_data = {
        'part_number': '', 'price': '', 'days_to_ship': '', 'minimum_order_qty': '',
        'inner_dia_d': '', 'outer_dia_d': '', 'width_b': '',
        'basic_load_rating_cr': '', 'basic_load_rating_cor': '', 'weight': '',
        'page_url': url
    }
    
    try:
        # Get text from each cell in the row
        cell_texts = []
        for cell in row_elements:
            cell_text = cell.text.strip()
            cell_texts.append(cell_text)
        
        # Map data based on headers
        for i, header in enumerate(headers):
            if i >= len(cell_texts):
                break
                
            header_lower = header.lower()
            value = cell_texts[i]
            
            # Part number detection
            if any(keyword in header_lower for keyword in ['part', 'model', 'number', 'code']):
                if value and len(value) > 2:  # Valid part number
                    row_data['part_number'] = value
                    
            # Price detection
            elif any(keyword in header_lower for keyword in ['price', 'cost', 'value']):
                if 'vnd' in value.lower():
                    row_data['price'] = value
                    
            # Days to ship detection
            elif any(keyword in header_lower for keyword in ['day', 'ship', 'delivery', 'lead']):
                if 'day' in value.lower():
                    row_data['days_to_ship'] = value
                    
            # Minimum order quantity
            elif any(keyword in header_lower for keyword in ['minimum', 'min', 'qty', 'quantity', 'order']):
                if any(unit in value.lower() for unit in ['piece', 'pcs', 'unit']):
                    row_data['minimum_order_qty'] = value
                    
            # Dimensions
            elif any(keyword in header_lower for keyword in ['inner', 'diameter', 'd']):
                if value and value.replace('.', '').replace(',', '').isdigit():
                    row_data['inner_dia_d'] = value
                    
            elif any(keyword in header_lower for keyword in ['outer', 'diameter', 'd']):
                if value and value.replace('.', '').replace(',', '').isdigit():
                    row_data['outer_dia_d'] = value
                    
            elif any(keyword in header_lower for keyword in ['width', 'b', 'thickness']):
                if value and value.replace('.', '').replace(',', '').isdigit():
                    row_data['width_b'] = value
                    
            # Load ratings
            elif any(keyword in header_lower for keyword in ['dynamic', 'cr', 'load']):
                if value and value.replace('.', '').replace(',', '').isdigit():
                    row_data['basic_load_rating_cr'] = value
                    
            elif any(keyword in header_lower for keyword in ['static', 'cor']):
                if value and value.replace('.', '').replace(',', '').isdigit():
                    row_data['basic_load_rating_cor'] = value
                    
            # Weight
            elif any(keyword in header_lower for keyword in ['weight', 'mass']):
                if value and value.replace('.', '').replace(',', '').isdigit():
                    row_data['weight'] = value
        
        # If no part number found in headers, try to find it in cell values
        if not row_data['part_number']:
            for cell_text in cell_texts:
                # Look for part number patterns
                if re.match(r'^[A-Z0-9\-]+$', cell_text) and len(cell_text) >= 3:
                    row_data['part_number'] = cell_text
                    break
                    
    except Exception as e:
        print(f"Error extracting row data: {e}")
        
    return row_data

def extract_from_tables_improved(driver, url):
    """Extract data from tables with improved row-by-row processing"""
    data = []
    
    try:
        # Find all tables
        tables = driver.find_elements(By.TAG_NAME, "table")
        print(f"Found {len(tables)} tables")
        
        for table_idx, table in enumerate(tables):
            try:
                # Get table headers
                headers = []
                header_row = table.find_elements(By.TAG_NAME, "thead")
                if header_row:
                    header_cells = header_row[0].find_elements(By.TAG_NAME, "th")
                    headers = [cell.text.strip() for cell in header_cells]
                
                # If no thead, try first row as header
                if not headers:
                    rows = table.find_elements(By.TAG_NAME, "tr")
                    if rows:
                        header_cells = rows[0].find_elements(By.TAG_NAME, "td")
                        headers = [cell.text.strip() for cell in header_cells]
                
                print(f"Table {table_idx + 1} headers: {headers}")
                
                # Process data rows
                rows = table.find_elements(By.TAG_NAME, "tr")
                for row_idx, row in enumerate(rows):
                    # Skip header row
                    if row_idx == 0 and headers:
                        continue
                        
                    try:
                        cells = row.find_elements(By.TAG_NAME, "td")
                        if cells:
                            row_data = extract_row_data(cells, headers, url)
                            if row_data['part_number']:  # Only add if we have a part number
                                data.append(row_data)
                                print(f"Extracted: {row_data['part_number']} - Price: {row_data['price']} - Days: {row_data['days_to_ship']}")
                    except Exception as e:
                        print(f"Error processing row {row_idx}: {e}")
                        continue
                        
            except Exception as e:
                print(f"Error processing table {table_idx}: {e}")
                continue
                
    except Exception as e:
        print(f"Error extracting from tables: {e}")
        
    return data

def extract_from_detail_container(driver, url):
    """Extract data specifically from detailTabContent and similar containers"""
    data = []
    
    try:
        # Look for detail containers
        containers = driver.find_elements(By.CSS_SELECTOR, "#deTabsContainer, .DetailTabs_productContentComplex__mi7Ez, #detailTabContent")
        
        for container in containers:
            try:
                # Find tables within the container
                tables = container.find_elements(By.TAG_NAME, "table")
                print(f"Found {len(tables)} tables in detail container")
                
                for table in tables:
                    table_data = extract_from_tables_improved(driver, url)
                    data.extend(table_data)
                    
            except Exception as e:
                print(f"Error processing detail container: {e}")
                continue
                
    except Exception as e:
        print(f"Error extracting from detail container: {e}")
        
    return data

def extract_from_text_context(driver, url):
    """Extract data from text with context around part numbers"""
    data = []
    
    try:
        # Get all text elements
        text_elements = driver.find_elements(By.XPATH, "//*[contains(text(), 'C-') or contains(text(), 'ZZ')]")
        
        for element in text_elements:
            try:
                text = element.text.strip()
                
                # Look for part number patterns
                part_matches = re.findall(r'C-[A-Z0-9]+ZZ', text)
                
                for part_number in part_matches:
                    row_data = {
                        'part_number': part_number, 'price': '', 'days_to_ship': '', 'minimum_order_qty': '',
                        'inner_dia_d': '', 'outer_dia_d': '', 'width_b': '',
                        'basic_load_rating_cr': '', 'basic_load_rating_cor': '', 'weight': '',
                        'page_url': url
                    }
                    
                    # Extract price
                    price_match = re.search(r'(\d{1,3}(?:,\d{3})*\s*VND)', text)
                    if price_match:
                        row_data['price'] = price_match.group(1)
                    
                    # Extract days to ship
                    if 'same day' in text.lower():
                        row_data['days_to_ship'] = 'same day'
                    elif 'day' in text.lower():
                        day_match = re.search(r'(\d+\s*day)', text.lower())
                        if day_match:
                            row_data['days_to_ship'] = day_match.group(1)
                    
                    # Extract minimum order quantity
                    qty_match = re.search(r'(\d+\s*piece)', text.lower())
                    if qty_match:
                        row_data['minimum_order_qty'] = qty_match.group(1)
                    
                    # Extract dimensions
                    inner_match = re.search(r'[d]\s*=\s*(\d+(?:\.\d+)?)', text)
                    if inner_match:
                        row_data['inner_dia_d'] = inner_match.group(1)
                    
                    outer_match = re.search(r'[D]\s*=\s*(\d+(?:\.\d+)?)', text)
                    if outer_match:
                        row_data['outer_dia_d'] = outer_match.group(1)
                    
                    width_match = re.search(r'[B]\s*=\s*(\d+(?:\.\d+)?)', text)
                    if width_match:
                        row_data['width_b'] = width_match.group(1)
                    
                    # Extract load ratings
                    cr_match = re.search(r'Cr\s*\(Dynamic\)\s*=\s*(\d+(?:,\d+)?)', text)
                    if cr_match:
                        row_data['basic_load_rating_cr'] = cr_match.group(1)
                    
                    cor_match = re.search(r'Cor\s*\(Static\)\s*=\s*(\d+(?:\.\d+)?)', text)
                    if cor_match:
                        row_data['basic_load_rating_cor'] = cor_match.group(1)
                    
                    # Extract weight
                    weight_match = re.search(r'Weight\s*=\s*(\d+(?:\.\d+)?)', text)
                    if weight_match:
                        row_data['weight'] = weight_match.group(1)
                    
                    data.append(row_data)
                    
            except Exception as e:
                print(f"Error processing text element: {e}")
                continue
                
    except Exception as e:
        print(f"Error extracting from text context: {e}")
        
    return data

def extract_comprehensive_data(driver, url):
    """Extract comprehensive data using improved strategies"""
    data = []
    
    try:
        print(f"Accessing: {url}")
        driver.get(url)
        time.sleep(5)
        
        # Scroll to trigger lazy loading
        driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
        time.sleep(2)
        driver.execute_script("window.scrollTo(0, 0);")
        time.sleep(2)
        
        # Strategy 1: Extract from tables with improved row processing
        table_data = extract_from_tables_improved(driver, url)
        data.extend(table_data)
        
        # Strategy 2: Extract from detail containers
        container_data = extract_from_detail_container(driver, url)
        data.extend(container_data)
        
        # Strategy 3: Extract from text context
        text_data = extract_from_text_context(driver, url)
        data.extend(text_data)
        
        print(f"Total extracted: {len(data)} rows from {url}")
        
    except Exception as e:
        print(f"Error extracting data from {url}: {e}")
        
    return data

def main():
    # Read URLs from Excel file
    excel_file = os.path.join(os.path.dirname(__file__), "ooo", "sameday9.xlsx")
    
    try:
        df = pd.read_excel(excel_file)
        print(f"Loaded {len(df)} URLs from {excel_file}")
        
        # Get URLs from the 'Product URL' column
        urls = df['Product URL'].dropna().unique().tolist()
        print(f"Found {len(urls)} unique URLs")
        
    except Exception as e:
        print(f"Error reading Excel file: {e}")
        return
    
    # Setup driver
    driver = setup_driver()
    if not driver:
        print("Failed to setup Chrome driver")
        return
    
    try:
        all_data = []
        
        for i, url in enumerate(urls):
            print(f"\nProcessing URL {i+1}/{len(urls)}")
            
            try:
                data = extract_comprehensive_data(driver, url)
                all_data.extend(data)
                
                # Small delay between requests
                time.sleep(1)
                
            except Exception as e:
                print(f"Error processing URL {url}: {e}")
                continue
        
        # Create DataFrame and remove duplicates
        if all_data:
            df_result = pd.DataFrame(all_data)
            df_result = df_result.drop_duplicates(subset=['part_number', 'page_url'], keep='first')
            
            print(f"\nFinal Results:")
            print(f"Total unique part numbers: {len(df_result)}")
            print(f"Part numbers with price: {len(df_result[df_result['price'] != ''])}")
            print(f"Part numbers with days to ship: {len(df_result[df_result['days_to_ship'] != ''])}")
            print(f"Part numbers with minimum order qty: {len(df_result[df_result['minimum_order_qty'] != ''])}")
            print(f"Part numbers with dimensions: {len(df_result[df_result['inner_dia_d'] != ''])}")
            print(f"Part numbers with load ratings: {len(df_result[df_result['basic_load_rating_cr'] != ''])}")
            
            # Save results
            output_csv = os.path.join(os.path.dirname(__file__), "ooo", "improved_comprehensive_data.csv")
            output_excel = os.path.join(os.path.dirname(__file__), "ooo", "improved_comprehensive_data.xlsx")
            
            df_result.to_csv(output_csv, index=False)
            df_result.to_excel(output_excel, index=False)
            
            print(f"\nResults saved to:")
            print(f"CSV: {output_csv}")
            print(f"Excel: {output_excel}")
            
            # Show sample data
            print("\nSample data:")
            print(df_result.head(10).to_string())
            
        else:
            print("No data extracted")
            
    finally:
        driver.quit()

if __name__ == "__main__":
    main()

