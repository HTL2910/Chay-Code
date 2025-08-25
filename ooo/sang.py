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

# def get_data_match_part_number(driver, index, part_number):
#     wait = WebDriverWait(driver, 60)
    
#     try:
#         dropdown_btn = wait.until(EC.element_to_be_clickable((By.XPATH, "//*[@id='codeList']")))
#         dropdown_btn.click()
#     except Exception as e:
#         print(f"Error clicking dropdown for {part_number}: {e}")
#         return {"Part Number": part_number, "Error": "Dropdown click failed"}

#     try:
#         table_Price_Days_Ship = wait.until(EC.presence_of_element_located(
#             (By.XPATH, "//*[@id='partNumberListTable']/div/div[2]/table"))
#         )
#         table_Part_Number=wait.until(EC.presence_of_element_located(
#             (By.XPATH, "//*[@id='partNumberListTable']/div/div[1]/table"))
#         )
#     except Exception as e:
#         print(f"Error locating table for {part_number}: {e}")
#         return {"Part Number": part_number, "Error": "Table not found"}
#     part_list=[]
#     link_list=[]
#     part_elements = table_Part_Number.find_elements(By.CLASS_NAME, "PartNumberColumn_data__gl8oY")
#     link = ""
#     for element in part_elements:
#         title = element.get_attribute("title")
#         link = element.get_attribute("href")
#         part_list.append(title)
#         link_list.append(link)
#         if title == part_number:
#             break
    
#     rows = table_Price_Days_Ship.find_elements(By.CSS_SELECTOR, "tr.PartNumberAsideColumns_dataRow__OUw8N")
#     spec_data = {"Index": index, "Part Number": part_list, "Price":part_number, "Days to Ship": "", "Link": link_list}
#     for row in rows:
#         try:
#             # part_number_elem = row.find_element(By.CSS_SELECTOR, ".PartNumberAsideColumns_partNumberCell__xyz")
            
#             price_elem = row.find_element(By.CSS_SELECTOR, ".PartNumberAsideColumns_dataCellBase__tIm9A")
#             days_to_ship_elem = row.find_element(By.CSS_SELECTOR, ".PartNumberAsideColumns_daysToShipDataCell__JRaMu")
                
#             # price = price_elem.text.strip()
#             days_to_ship = days_to_ship_elem.text.strip()
#             # spec_data["Price"] = price
#             spec_data["Days to Ship"] = days_to_ship
            
#         except Exception as e:
#             print(f"Error extracting data for {part_number}: {e}")
#             continue

#     print("spec_data:", spec_data)
#     return spec_data
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
    time.sleep(5)
    part_numbers, link_numbers = extract_all_part_numbers(driver)
    print(f"Tìm thấy {len(part_numbers)} part numbers.")
    print(f"Tìm thấy {len(link_numbers)} link numbers.")

    # all_data = []
    # for idx, pn in enumerate(part_numbers, start=1):
    #     print(f"({idx}/{len(part_numbers)}) Đang lấy dữ liệu: {pn}")
    #     # data = extract_specifications(driver, pn, max_retry=3)
    #     data=get_data_match_part_number(driver,idx, pn)
    #     data["Part Number"] = pn
    #     all_data.append(data)
    #     time.sleep(1)
        
    # print("all_data:", all_data)
    driver.quit()

    # # Lưu ra Excel
    # if all_data:
    #     df = pd.DataFrame(all_data)
    #     output_file = "misumi_bearings.xlsx"
    #     df.to_excel(output_file, index=False)
    #     print(f"✅ Đã lưu dữ liệu vào {output_file}")
    # else:
    #     print("⚠ Không lấy được dữ liệu nào.")


if __name__ == "__main__":
    main()