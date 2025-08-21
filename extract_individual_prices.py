import os
import time
import pandas as pd
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
from urllib.parse import urljoin, urlparse, parse_qs

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

def extract_price_from_part_url(driver, part_number, base_url):
    """Extract price from individual part number URL"""
    try:
        # Try to construct part number URL
        # Example: https://vn.misumi-ec.com/vona2/detail/110302648470/?partNumber=EB13
        parsed_url = urlparse(base_url)
        query_params = parse_qs(parsed_url.query)
        
        # Add part number to URL
        query_params['partNumber'] = [part_number]
        
        # Reconstruct URL
        part_url = f"{parsed_url.scheme}://{parsed_url.netloc}{parsed_url.path}?"
        part_url += "&".join([f"{k}={v[0]}" for k, v in query_params.items()])
        
        print(f"Trying to access: {part_url}")
        driver.get(part_url)
        
        # Wait for page to load
        time.sleep(3)
        
        # Strategy 1: Look for price in JSON-LD data
        try:
            page_source = driver.page_source
            import re
            
            # Look for JSON-LD with price information
            json_pattern = r'"lowPrice":\s*(\d+).*?"highPrice":\s*(\d+).*?"priceCurrency":\s*"([^"]+)"'
            price_match = re.search(json_pattern, page_source, re.DOTALL)
            if price_match:
                low_price = price_match.group(1)
                high_price = price_match.group(2)
                currency = price_match.group(3)
                if low_price == high_price:
                    return f"{low_price} {currency}"
                else:
                    return f"{low_price}-{high_price} {currency}"
        except Exception as e:
            print(f"Error extracting price from JSON: {e}")
        
        # Strategy 2: Look for price elements
        price_elements = driver.find_elements(By.XPATH, "//*[contains(text(), '₫') or contains(text(), '$') or contains(text(), 'VND')]")
        for elem in price_elements:
            text = elem.text.strip()
            if text and any(c.isdigit() for c in text):
                # Check if it looks like a price
                if re.search(r'[\d,]+\.?\d*\s*[₫$VND]', text):
                    return text
        
        # Strategy 3: Look for price in specific classes
        price_classes = [
            "PartNumberAsideColumns_data__jikjP",
            "price",
            "Price",
            "cost",
            "Cost"
        ]
        
        for class_name in price_classes:
            try:
                elements = driver.find_elements(By.CLASS_NAME, class_name)
                for elem in elements:
                    text = elem.text.strip()
                    if text and any(c.isdigit() for c in text):
                        if re.search(r'[\d,]+\.?\d*\s*[₫$VND]', text):
                            return text
            except:
                continue
        
        return "Price not found"
        
    except Exception as e:
        print(f"Error extracting price for {part_number}: {e}")
        return "Error"

def main():
    # Read the existing CSV with part numbers
    input_csv = os.path.join(os.path.dirname(__file__), "part_number_rows_extracted.csv")
    if not os.path.exists(input_csv):
        print(f"Input CSV not found: {input_csv}")
        return
    
    df = pd.read_csv(input_csv)
    
    # Filter to get unique part numbers (remove duplicates and empty ones)
    part_numbers = df['part_number'].dropna().unique()
    part_numbers = [pn for pn in part_numbers if pn and pn != "" and not pn.startswith("SPEC-")]
    
    print(f"Found {len(part_numbers)} unique part numbers to process")
    print(f"Sample part numbers: {part_numbers[:10]}")
    
    # Get base URL from first row
    base_url = df['page_url'].iloc[0] if not df.empty else ""
    if not base_url:
        print("No base URL found")
        return
    
    driver = setup_driver()
    if not driver:
        return
    
    results = []
    
    try:
        for i, part_number in enumerate(part_numbers[:20]):  # Limit to first 20 for testing
            print(f"[{i+1}/{min(20, len(part_numbers))}] Processing part number: {part_number}")
            
            price = extract_price_from_part_url(driver, part_number, base_url)
            
            result = {
                "part_number": part_number,
                "price": price,
                "base_url": base_url
            }
            results.append(result)
            
            print(f"  Price for {part_number}: {price}")
            time.sleep(1)  # Be nice to the server
    
    finally:
        driver.quit()
    
    # Save results
    output_csv = os.path.join(os.path.dirname(__file__), "individual_prices.csv")
    if results:
        out_df = pd.DataFrame(results)
        out_df.to_csv(output_csv, index=False, encoding="utf-8-sig")
        print(f"Saved {len(results)} price results to {output_csv}")
        print("Sample results:")
        print(out_df.head())
    else:
        print("No price data extracted")

if __name__ == "__main__":
    main()
