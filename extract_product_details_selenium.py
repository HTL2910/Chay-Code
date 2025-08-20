import os
import re
import time
import pandas as pd
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

def get_product_details_selenium(driver, product_link, base_url):
    try:
        full_url = urljoin(base_url, product_link)
        print(f"  Accessing URL: {full_url}")
        driver.get(full_url)
        time.sleep(3)
        WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.TAG_NAME, "title"))
        )
        page_title = driver.title
        print(f"  Page title: {page_title}")

        description = ''
        try:
            description_element = driver.find_element(By.CLASS_NAME, "style_simple_detail__Tzjyy")
            description = description_element.text.strip()
            print(f"  Description: {description[:50]}..." if description else "  No description found")
        except:
            print("  No description found")

        image_link = ''
        try:
            image_element = driver.find_element(By.CLASS_NAME, "MainProductImage_zoomImage___u6yj")
            image_src = image_element.get_attribute('src')
            if image_src:
                image_link = urljoin(base_url, image_src)
                print(f"  Image found: {image_link[:50]}...")
            else:
                print("  No image src found")
        except:
            print("  No image element found")

        part_numbers_tab = None
        try:
            time.sleep(5)
            all_tabs = driver.find_elements(By.CLASS_NAME, "DetailTab_itemLink__IU08c")
            print(f"  Found {len(all_tabs)} detail tabs")
            for i, tab in enumerate(all_tabs):
                tab_text = tab.text.strip()
                tab_href = tab.get_attribute('href')
                print(f"    Tab {i+1}: '{tab_text}' -> {tab_href}")
            part_numbers_tab = None
            for tab in all_tabs:
                if "Part Numbers" in tab.text or "codeList" in tab.get_attribute('id'):
                    part_numbers_tab = tab
                    break
            if part_numbers_tab:
                print(f"  Found Part Numbers tab: {part_numbers_tab.text}")
                driver.execute_script("arguments[0].scrollIntoView(true);", part_numbers_tab)
                time.sleep(1)
                driver.execute_script("arguments[0].click();", part_numbers_tab)
                print("  Clicked on Part Numbers tab")
                time.sleep(5)
                part_numbers_content = None
                try:
                    part_numbers_content = driver.find_element(By.CLASS_NAME, "PartNumberList_mainOuter__d74Qg")
                    print("  Found Part Numbers content with PartNumberList_mainOuter__d74Qg")
                except:
                    pass
                if not part_numbers_content:
                    try:
                        part_numbers_content = driver.find_element(By.CLASS_NAME, "PartNumberList_main__klm4X")
                        print("  Found Part Numbers content with PartNumberList_main__klm4X")
                    except:
                        pass
                if not part_numbers_content:
                    try:
                        part_number_elements = driver.find_elements(By.XPATH, "//*[contains(@class, 'PartNumber')]")
                        if part_number_elements:
                            part_numbers_content = part_number_elements[0]
                            print(f"  Found Part Numbers content with PartNumber class: {part_numbers_content.get_attribute('class')}")
                    except:
                        pass
                if not part_numbers_content:
                    try:
                        tables = driver.find_elements(By.TAG_NAME, "table")
                        for table in tables:
                            if "PartNumber" in table.get_attribute('class', ''):
                                part_numbers_content = table
                                print(f"  Found Part Numbers table: {table.get_attribute('class')}")
                                break
                    except:
                        pass
                if part_numbers_content:
                    return extract_part_numbers_from_selenium(part_numbers_content, {
                        'Description': description,
                        'Image Link': image_link,
                        'Product URL': full_url
                    })
                else:
                    print("  Could not find Part Numbers content with any approach")
                    print("  Trying to extract part numbers from entire page")
                    return extract_part_numbers_from_selenium(driver, {
                        'Description': description,
                        'Image Link': image_link,
                        'Product URL': full_url
                    })
            else:
                print("  Could not find Part Numbers tab")
        except Exception as e:
            print(f"  Error with Part Numbers tab: {e}")
            try:
                part_numbers_tab = driver.find_element(By.CLASS_NAME, "DetailTab_itemLink__IU08c")
                print(f"  Found alternative Part Numbers tab: {part_numbers_tab is not None}")
                driver.execute_script("arguments[0].click();", part_numbers_tab)
                print("  Clicked on alternative Part Numbers tab")
                time.sleep(3)
                try:
                    part_numbers_content = driver.find_element(By.CLASS_NAME, "PartNumberList_mainOuter__d74Qg")
                    print(f"  Found Part Numbers content: {part_numbers_content is not None}")
                    if part_numbers_content:
                        return extract_part_numbers_from_selenium(part_numbers_content, {
                            'Description': description,
                            'Image Link': image_link,
                            'Product URL': full_url
                        })
                except:
                    print("  Could not find Part Numbers content with PartNumberList_mainOuter__d74Qg class")
                    try:
                        all_elements = driver.find_elements(By.XPATH, "//*[contains(@class, 'PartNumber')]")
                        print(f"  Found {len(all_elements)} elements with 'PartNumber' in class name")
                        for i, elem in enumerate(all_elements):
                            class_name = elem.get_attribute('class')
                            print(f"    Element {i+1} class: {class_name}")
                    except:
                        print("  Error searching for PartNumber elements")
                    try:
                        all_tables = driver.find_elements(By.TAG_NAME, "table")
                        print(f"  Found {len(all_tables)} tables on the page")
                        for i, table in enumerate(all_tables):
                            table_class = table.get_attribute('class')
                            print(f"    Table {i+1} class: {table_class}")
                            if table_class and 'PartNumber' in table_class:
                                print(f"    Found table with PartNumber class: {table_class}")
                                return extract_part_numbers_from_selenium(table, {
                                    'Description': description,
                                    'Image Link': image_link,
                                    'Product URL': full_url
                                })
                    except:
                        print("  Error searching for tables")
            except Exception as e2:
                print(f"  Error with alternative approach: {e2}")
        part_number_match = re.search(r'/detail/(\d+)/', product_link)
        main_part_number = part_number_match.group(1) if part_number_match else ''
        return [{
            'Part Number': main_part_number,
            'Description': description,
            'Image Link': image_link,
            'Product URL': full_url
        }]
    except Exception as e:
        print(f"Error extracting details from {product_link}: {e}")
        return [{
            'Part Number': '',
            'Description': '',
            'Image Link': '',
            'Product URL': urljoin(base_url, product_link),
            'Error': str(e)
        }]

def extract_part_numbers_from_selenium(part_numbers_content, base_info):
    part_numbers_data = []
    try:
        html_content = part_numbers_content.get_attribute('innerHTML')
        print(f"    HTML content length: {len(html_content)}")
        print(f"    Text content: {part_numbers_content.text[:200]}...")
        part_number_options = part_numbers_content.find_elements(By.CLASS_NAME, "PartNumberDropDownList_partNumberOption__KnDz0")
        print(f"    Found {len(part_number_options)} part number options")
        for i, option in enumerate(part_number_options):
            try:
                part_number = option.text.strip()
                if part_number and len(part_number) >= 3:
                    print(f"      Part Number {i+1}: {part_number}")
                    part_info = base_info.copy()
                    part_info['Part Number'] = part_number
                    part_numbers_data.append(part_info)
            except Exception as e:
                print(f"      Error processing part number option {i+1}: {e}")
        if not part_numbers_data:
            print("    No part numbers found from dropdown, trying link approach")
            part_number_links = part_numbers_content.find_elements(By.CLASS_NAME, "PartNumberColumn_partNumberLink___bNpQ")
            print(f"    Found {len(part_number_links)} part number links")
            for i, link in enumerate(part_number_links):
                try:
                    part_number = link.text.strip()
                    part_number_url = link.get_attribute('href')
                    part_number_title = link.get_attribute('title')
                    print(f"      Part Number {i+1}: {part_number}")
                    print(f"        URL: {part_number_url}")
                    print(f"        Title: {part_number_title}")
                    part_info = base_info.copy()
                    part_info['Part Number'] = part_number
                    part_info['Part Number URL'] = part_number_url
                    part_info['Part Number Title'] = part_number_title
                    part_numbers_data.append(part_info)
                except Exception as e:
                    print(f"      Error processing part number link {i+1}: {e}")
        if not part_numbers_data:
            print("    No part number links found, trying table approach")
            tables = part_numbers_content.find_elements(By.TAG_NAME, "table")
            print(f"    Found {len(tables)} tables")
            for i, table in enumerate(tables):
                print(f"    Processing table {i+1}")
                rows = table.find_elements(By.TAG_NAME, "tr")
                print(f"      Found {len(rows)} rows in table {i+1}")
                for j, row in enumerate(rows):
                    cells = row.find_elements(By.TAG_NAME, "td")
                    if len(cells) >= 1:
                        part_number = ''
                        row_data = {}
                        for k, cell in enumerate(cells):
                            cell_text = cell.text.strip()
                            print(f"        Cell {k}: '{cell_text}'")
                            if re.match(r'^[A-Z0-9\-]+$', cell_text) and len(cell_text) >= 5:
                                part_number = cell_text
                                row_data[f'Column_{k}'] = cell_text
                            else:
                                row_data[f'Column_{k}'] = cell_text
                        if part_number:
                            part_info = base_info.copy()
                            part_info['Part Number'] = part_number
                            part_info['Row Data'] = str(row_data)
                            part_numbers_data.append(part_info)
                            print(f"    Found part number: {part_number}")
        if not part_numbers_data:
            print("    No tables found, looking for text patterns")
            all_text = part_numbers_content.text
            part_number_matches = re.findall(r'\b[A-Z0-9\-]{5,20}\b', all_text)
            for part_number in part_number_matches:
                if not re.match(r'^\d+$', part_number) and not re.match(r'^[A-Z]{1,3}$', part_number):
                    part_info = base_info.copy()
                    part_info['Part Number'] = part_number
                    part_numbers_data.append(part_info)
                    print(f"    Found part number from text: {part_number}")
        if not part_numbers_data:
            part_info = base_info.copy()
            part_info['Part Number'] = ''
            part_numbers_data.append(part_info)
            print("    No part numbers found, using base info")
        return part_numbers_data
    except Exception as e:
        print(f"Error extracting part numbers from detail: {e}")
        part_info = base_info.copy()
        part_info['Part Number'] = ''
        part_info['Error'] = str(e)
        return [part_info]

def process_product_links_selenium(csv_file_path, base_url):
    """
    Đọc file CSV và lấy thông tin chi tiết sản phẩm bằng Selenium.
    Sửa lại để lấy dữ liệu của 10 file trong thư mục chay.
    """
    try:
        # Lấy danh sách tất cả file csv trong thư mục chay
        chay_dir = r'C:\Users\abc\Pictures\code\chay'
        csv_files = [os.path.join(chay_dir, f) for f in os.listdir(chay_dir) if f.lower().endswith('.csv')]
        csv_files = sorted(csv_files)[:10]  # Lấy 10 file đầu tiên

        print(f"Found {len(csv_files)} CSV files in {chay_dir}:")
        for f in csv_files:
            print(f"  {f}")

        all_details = []
        driver = setup_driver()
        if not driver:
            return pd.DataFrame()

        try:
            for file_idx, csv_file in enumerate(csv_files):
                print(f"\n=== Processing file {file_idx+1}/{len(csv_files)}: {csv_file} ===")
                df = pd.read_csv(csv_file)
                # Kiểm tra cả 'Product Link' và 'Product URL'
                product_link_column = None
                if 'Product Link' in df.columns:
                    product_link_column = 'Product Link'
                elif 'Product URL' in df.columns:
                    product_link_column = 'Product URL'
                else:
                    print(f"Error: Neither 'Product Link' nor 'Product URL' column found in {csv_file}")
                    print(f"Available columns: {df.columns.tolist()}")
                    continue
                print(f"  Found {len(df)} products in file")
                for index, row in df.iterrows():
                    product_link = row[product_link_column]
                    part_number = row.get('Part Number', '')
                    print(f"Processing product {index + 1}/{len(df)}: {part_number}")
                    details_list = get_product_details_selenium(driver, product_link, base_url)
                    for details in details_list:
                        details.update({
                            'Original Part Number': part_number,
                            'Original Product Name': row.get('Product Name', ''),
                            'Original Price': row.get('Price', ''),
                            'Original Lead Time': row.get('Lead Time', ''),
                            'Original Page': row.get('Page', ''),
                            'Source File': os.path.basename(csv_file)
                        })
                        all_details.append(details)
                    time.sleep(2)
        finally:
            driver.quit()
        return pd.DataFrame(all_details)
    except Exception as e:
        print(f"Error processing CSV files: {e}")
        return pd.DataFrame()

def save_to_excel(df, output_path):
    try:
        df.to_excel(output_path, index=False, engine='openpyxl')
        print(f"Data saved to {output_path}")
    except Exception as e:
        print(f"Error saving to Excel: {e}")

def save_to_csv(df, output_path):
    try:
        df.to_csv(output_path, index=False, encoding='utf-8-sig')
        print(f"Data saved to {output_path}")
    except Exception as e:
        print(f"Error saving to CSV: {e}")

def main():
    """
    Main function to extract detailed product information using Selenium
    """
    base_url = "https://vn.misumi-ec.com"
    # Không dùng file CSV đơn lẻ nữa, sẽ lấy 10 file trong thư mục chay
    output_directory = r'c:\Users\abc\Pictures\code'

    print("Starting detailed product information extraction using Selenium...")
    print(f"Base URL: {base_url}")
    print(f"Input directory: C:\\Users\\abc\\Pictures\\code\\chay")

    chay_dir = r'C:\Users\abc\Pictures\code\chay'
    if not os.path.exists(chay_dir):
        print(f"Error: {chay_dir} not found!")
        return

    df_details = process_product_links_selenium(None, base_url)

    if df_details.empty:
        print("No product details extracted!")
        return

    print(f"\nTotal products processed: {len(df_details)}")
    print("\nSample data:")
    print(df_details.head())

    excel_path = os.path.join(output_directory, 'product_details_selenium.xlsx')
    save_to_excel(df_details, excel_path)

    csv_path = os.path.join(output_directory, 'product_details_selenium.csv')
    save_to_csv(df_details, csv_path)

    print(f"\nSummary:")
    print(f"Total products processed: {len(df_details)}")
    error_count = 0
    if 'Error' in df_details.columns:
        error_count = len(df_details[df_details['Error'].notna() & (df_details['Error'] != '')])
    print(f"Products with errors: {error_count}")
    print(f"Products with images: {len(df_details[df_details['Image Link'] != ''])}")
    print(f"Products with descriptions: {len(df_details[df_details['Description'] != ''])}")
    print(f"Unique part numbers found: {df_details['Part Number'].nunique()}")

    print(f"\nColumn statistics:")
    for column in ['Description', 'Image Link']:
        non_empty_count = len(df_details[df_details[column] != ''])
        print(f"  {column}: {non_empty_count}/{len(df_details)} products")

if __name__ == "__main__":
    main()
