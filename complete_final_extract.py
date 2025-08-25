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

def extract_complete_data(driver, url):
    """Extract complete data including technical specs and price/availability"""
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
        
        # Get all part numbers from the page first
        page_text = driver.find_element(By.TAG_NAME, "body").text
        all_part_numbers = re.findall(r'[A-Z0-9\-]+ZZ', page_text)#Sửa lại nha: Áp dụng part number đuôi ZZ
        unique_part_numbers = list(set(all_part_numbers))
        
        print(f"Found {len(unique_part_numbers)} unique part numbers")
        
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
                # Get 1000 characters around the part number
                start = max(0, part_index - 500)
                end = min(len(page_text), part_index + len(part_number) + 500)
                context = page_text[start:end]
                
                # Extract price from context
                price_match = re.search(r'(\d{1,3}(?:,\d{3})*\s*VND)', context)
                if price_match:
                    row_data['price'] = price_match.group(1)
                
                # Extract days to ship from context
                if 'same day' in context.lower():
                    row_data['days_to_ship'] = 'same day'
                elif 'day' in context.lower():
                    day_match = re.search(r'(\d+\s*day)', context.lower())
                    if day_match:
                        row_data['days_to_ship'] = day_match.group(1)
                
                # Extract minimum order quantity from context
                qty_match = re.search(r'(\d+\s*piece)', context.lower())
                if qty_match:
                    row_data['minimum_order_qty'] = qty_match.group(1)
            
            # Now extract technical specifications from tables
            tables = driver.find_elements(By.TAG_NAME, "table")
            for table in tables:
                try:
                    rows = table.find_elements(By.TAG_NAME, "tr")
                    if len(rows) < 2:
                        continue
                    
                    # Get headers
                    headers = []
                    header_row = rows[0]
                    header_cells = header_row.find_elements(By.TAG_NAME, "th") + header_row.find_elements(By.TAG_NAME, "td")
                    headers = [cell.text.strip() for cell in header_cells]
                    
                    # Look for the row containing this part number
                    for row in rows[1:]:  # Skip header row
                        cells = row.find_elements(By.TAG_NAME, "td")
                        cell_texts = [cell.text.strip() for cell in cells]
                        
                        # Check if this row contains our part number
                        if part_number in cell_texts:
                            # Map data based on headers
                            for i, header in enumerate(headers):
                                if i >= len(cell_texts):
                                    break
                                    
                                header_lower = header.lower()
                                value = cell_texts[i]
                                
                                # Map technical specifications
                                if 'inner' in header_lower and 'dia' in header_lower:
                                    if value and value.replace('.', '').replace(',', '').isdigit():
                                        row_data['inner_dia_d'] = value
                                elif 'outer' in header_lower and 'dia' in header_lower:
                                    if value and value.replace('.', '').replace(',', '').isdigit():
                                        row_data['outer_dia_d'] = value
                                elif 'width' in header_lower or 'b' in header_lower:
                                    if value and value.replace('.', '').replace(',', '').isdigit():
                                        row_data['width_b'] = value
                                elif 'dynamic' in header_lower or 'cr' in header_lower:
                                    if value and value.replace('.', '').replace(',', '').isdigit():
                                        row_data['basic_load_rating_cr'] = value
                                elif 'static' in header_lower or 'cor' in header_lower:
                                    if value and value.replace('.', '').replace(',', '').isdigit():
                                        row_data['basic_load_rating_cor'] = value
                                elif 'weight' in header_lower or 'mass' in header_lower:
                                    if value and value.replace('.', '').replace(',', '').isdigit():
                                        row_data['weight'] = value
                            
                            break  # Found the row, no need to continue
                            
                except Exception as e:
                    print(f"Error processing table: {e}")
                    continue
            
            # Only add if we have at least some data
            if any([row_data['price'], row_data['days_to_ship'], row_data['minimum_order_qty'], 
                   row_data['inner_dia_d'], row_data['outer_dia_d'], row_data['width_b'], 
                   row_data['basic_load_rating_cr'], row_data['basic_load_rating_cor'], row_data['weight']]):
                data.append(row_data)
                print(f"Extracted complete data: {part_number} - Price: {row_data['price']} - Days: {row_data['days_to_ship']} - Inner: {row_data['inner_dia_d']} - Outer: {row_data['outer_dia_d']}")
        
        print(f"Total extracted: {len(data)} complete rows from {url}")
        
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
                data = extract_complete_data(driver, url)
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
            print(f"Part numbers with inner diameter: {len(df_result[df_result['inner_dia_d'] != ''])}")
            print(f"Part numbers with outer diameter: {len(df_result[df_result['outer_dia_d'] != ''])}")
            print(f"Part numbers with width: {len(df_result[df_result['width_b'] != ''])}")
            print(f"Part numbers with load rating Cr: {len(df_result[df_result['basic_load_rating_cr'] != ''])}")
            print(f"Part numbers with load rating Cor: {len(df_result[df_result['basic_load_rating_cor'] != ''])}")
            print(f"Part numbers with weight: {len(df_result[df_result['weight'] != ''])}")
            
            # Save results
            output_csv = os.path.join(os.path.dirname(__file__), "ooo", "complete_final_data.csv")
            output_excel = os.path.join(os.path.dirname(__file__), "ooo", "complete_final_data.xlsx")
            
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
