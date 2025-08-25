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
    time.sleep(5)
    
    # Scroll to trigger lazy loading
    driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
    time.sleep(2)
    driver.execute_script("window.scrollTo(0, 0);")
    time.sleep(2)

    try:
        # Chờ đúng nút có id 'codeList'
        dropdown_btn = wait.until(EC.element_to_be_clickable((By.XPATH, "//*[@id='codeList']")))
        time.sleep(3)
        dropdown_btn.click()
        time.sleep(3)
    except Exception as e:
        print(f"Error clicking dropdown: {e}")
        return [], [], []

    part_numbers = []
    prices = []
    links = []
    
    try:
        # Thử tìm bảng với các selector khác nhau
        table_selectors = [
            "//*[@id='partNumberListTable']/div/div[1]/table",
            "//table[contains(@class, 'PartNumberColumn')]",
            "//div[contains(@class, 'PartNumberColumn')]//table",
            "//table[contains(@class, 'table')]"
        ]
        
        table = None
        for selector in table_selectors:
            try:
                table = wait.until(EC.presence_of_element_located((By.XPATH, selector)))
                print(f"Found table with selector: {selector}")
                break
            except:
                continue
        
        if not table:
            print("Could not find table with any selector")
            return [], [], []
        
        # Tìm tất cả các hàng
        rows = table.find_elements(By.TAG_NAME, "tr")
        print(f"Found {len(rows)} rows")
        
        for row in rows:
            try:
                # Tìm part number
                part_number_elements = row.find_elements(By.TAG_NAME, "a")
                if part_number_elements:
                    part_number = part_number_elements[0].get_attribute("title") or part_number_elements[0].text.strip()
                    link = part_number_elements[0].get_attribute("href")
                    
                    if part_number and part_number not in part_numbers:
                        part_numbers.append(part_number)
                        links.append(link)
                        
                        # Tìm price trong cùng hàng
                        price_cells = row.find_elements(By.TAG_NAME, "td")
                        price = ""
                        if len(price_cells) > 1:
                            price = price_cells[1].text.strip()
                        prices.append(price)
                        
            except Exception as e:
                print(f"Error processing row: {e}")
                continue
                
    except Exception as e:
        print(f"Error extracting data: {e}")
        return [], [], []

    print("part_numbers:", part_numbers)
    print("prices:", prices)
    print("part_numbers length:", len(part_numbers))
    print("links:", links)
    print("links length:", len(links))

    return part_numbers, prices, links


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

def get_data_match_part_number(driver, index, part_number, price, link):
    wait = WebDriverWait(driver, 60)
    
    spec_data = {"Index": index, "Part Number": part_number, "Price": price, "Days to Ship": "", "Link": link}
    
    try:
        # Thử tìm days to ship từ bảng
        table_selectors = [
            "//*[@id='partNumberListTable']/div/div[2]/table",
            "//table[contains(@class, 'PartNumberAsideColumns')]",
            "//div[contains(@class, 'PartNumberAsideColumns')]//table"
        ]
        
        days_to_ship = ""
        for selector in table_selectors:
            try:
                table = wait.until(EC.presence_of_element_located((By.XPATH, selector)))
                rows = table.find_elements(By.TAG_NAME, "tr")
                
                for row in rows:
                    try:
                        cells = row.find_elements(By.TAG_NAME, "td")
                        if len(cells) >= 2:
                            # Thử tìm days to ship trong cột cuối
                            days_to_ship = cells[-1].text.strip()
                            if days_to_ship and "day" in days_to_ship.lower():
                                spec_data["Days to Ship"] = days_to_ship
                                break
                    except:
                        continue
                        
                if spec_data["Days to Ship"]:
                    break
                    
            except:
                continue
                
    except Exception as e:
        print(f"Error getting days to ship for {part_number}: {e}")

    print("spec_data:", spec_data)
    return spec_data
# ====== MAIN ======
def main():
    url = "https://vn.misumi-ec.com/vona2/detail/110310367019/?KWSearch=bearing&searchFlow=results2products&list=PageSearchResult"

    # Khởi tạo Chrome
    driver = setup_driver()
    if not driver:
        print("Failed to setup Chrome driver")
        return
    
    driver.maximize_window()
    driver.get(url)

    print("Đang lấy danh sách Part Numbers...")
    part_numbers, prices, links = extract_all_part_numbers(driver)
    print(f"Tìm thấy {len(part_numbers)} part numbers.")
    
    if not part_numbers:
        print("Không tìm thấy part numbers nào!")
        driver.quit()
        return
        
    all_data = []
    for idx, pn in enumerate(part_numbers, start=1):
        print(f"({idx}/{len(part_numbers)}) Đang lấy dữ liệu: {pn}")
        try:
            price = prices[idx-1] if idx-1 < len(prices) else ""
            link = links[idx-1] if idx-1 < len(links) else ""
            data = get_data_match_part_number(driver, idx, pn, price, link)
            all_data.append(data)
        except Exception as e:
            print(f"Error processing {pn}: {e}")
            all_data.append({"Index": idx, "Part Number": pn, "Price": "", "Days to Ship": "", "Link": "", "Error": str(e)})
        time.sleep(1)
        
    print("all_data:", all_data)
    driver.quit()

    # # Lưu ra Excel
    if all_data:
        df = pd.DataFrame(all_data)
        output_file = "misumi_bearings_A1.xlsx"
        df.to_excel(output_file, index=False)
        print(f"✅ Đã lưu dữ liệu vào {output_file}")
    else:
        print("⚠ Không lấy được dữ liệu nào.")


if __name__ == "__main__":
    main()