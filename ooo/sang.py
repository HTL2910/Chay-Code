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


def get_data_prices_days_ship(driver):
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
    prices=[]
    days_to_ship=[]
    table_price_days_ship=wait.until(EC.presence_of_element_located((By.CLASS_NAME, "PartNumberAsideColumns_table__6fKVE")))
    rows=table_price_days_ship.find_elements(By.CLASS_NAME, "PartNumberAsideColumns_dataRow__OUw8N")
    for row in rows:
        #lấy giá
        price_cell=row.find_element(By.CLASS_NAME, "PartNumberAsideColumns_dataCellBase__tIm9A")
        price=price_cell.find_element(By.CLASS_NAME, "PartNumberAsideColumns_data__jikjP").find_element(By.TAG_NAME, "span").text.strip()
        prices.append(price)
        #lấy ngày giao hàng
        day_to_ship_cell=row.find_element(By.CLASS_NAME, "PartNumberAsideColumns_daysToShipDataCell__JRaMu")
        day_to_ship=day_to_ship_cell.find_element(By.CLASS_NAME, "PartNumberAsideColumns_data__jikjP").find_element(By.TAG_NAME, "span").text.strip()
        days_to_ship.append(day_to_ship)
    print("prices:", prices)
    print("days_to_ship:", days_to_ship)
    return prices, days_to_ship

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
    prices, days_to_ship = get_data_prices_days_ship(driver)
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