import time
import pandas as pd
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
from bs4 import BeautifulSoup

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
def get_other_data(driver):
    wait = WebDriverWait(driver, 60)
    time.sleep(5)
    driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
    time.sleep(2)
    driver.execute_script("window.scrollTo(0, 0);")
    time.sleep(2)
    dropdown_btn = wait.until(EC.element_to_be_clickable((By.XPATH, "//*[@id='detailTabs']/div/div/div/ul/li[2]")))
    time.sleep(5)
    dropdown_btn.click()
    time.sleep(5)
    minimum_order_qty=[]
    volumn_discount=[]
    inner_dia_d=[]
    outer_dia_d=[]
    width_b=[]
    basic_load_rating_cr=[]
    basic_load_rating_cor=[]
    weight=[]
    table_other_data = wait.until(
        EC.presence_of_element_located((By.CLASS_NAME, "PartNumberSpecColumns_tableBase__VK5Nd"))
    )

    rows = table_other_data.find_elements(By.CLASS_NAME, "PartNumberSpecColumns_dataRow__M4B4a")

    # for row in rows:
    #     print("----- outerHTML -----")
    #     print(row.get_attribute("outerHTML"))   # toàn bộ <tr>...</tr>
        
    #     print("----- innerHTML -----")
    #     print(row.get_attribute("innerHTML"))   # chỉ lấy phần bên trong <tr>...</tr>
        
    #     print("----- text -----")
    #     print(row.text) 

    for row in rows:
        html = row.get_attribute("innerHTML")
        soup = BeautifulSoup(html, "html.parser")
        values = [div.get_text(strip=True) for div in soup.select("div.PartNumberSpecCells_data__u6ZZX")]
        minimum_order_qty.append(values[0])
        volumn_discount.append(values[1])
        inner_dia_d.append(values[2])
        outer_dia_d.append(values[3])
        width_b.append(values[4])
        basic_load_rating_cr.append(values[5])
        basic_load_rating_cor.append(values[6])
        weight.append(values[7])
    print("minimum_order_qty:", minimum_order_qty)
    print("volumn_discount:", volumn_discount)
    print("inner_dia_d:", inner_dia_d)
    print("outer_dia_d:", outer_dia_d)
    print("width_b:", width_b)
    print("basic_load_rating_cr:", basic_load_rating_cr)
    print("basic_load_rating_cor:", basic_load_rating_cor)
    print("weight:", weight)

    return minimum_order_qty, volumn_discount, inner_dia_d, outer_dia_d, width_b, basic_load_rating_cr, basic_load_rating_cor, weight
# ====== MAIN ======
def main():
    url = "https://vn.misumi-ec.com/vona2/detail/110310367019/?KWSearch=bearing&searchFlow=results2products&list=PageSearchResult"

    # Khởi tạo Chrome
    driver = setup_driver()
    if not driver:
        print("Failed to setup Chrome driver")
        return
    all_data=[]
    driver.maximize_window()
    driver.get(url)
    print("Đang lấy danh sách Part Numbers...")
    time.sleep(5)
    part_numbers, link_numbers = extract_all_part_numbers(driver)
    print(f"Tìm thấy {len(part_numbers)} part numbers.")
    print(f"Tìm thấy {len(link_numbers)} link numbers.")
    prices, days_to_ship = get_data_prices_days_ship(driver)
    minimum_order_qty, volumn_discount, inner_dia_d, outer_dia_d, width_b, basic_load_rating_cr, basic_load_rating_cor, weight = get_other_data(driver)  
    for i in range(len(part_numbers)):
        all_data.append({
            "Part Number": part_numbers[i],
            "Price": prices[i],
            "Days to Ship": days_to_ship[i],
            "Link": link_numbers[i],
            "Minimum Order Qty": minimum_order_qty[i],
            "Volumn Discount": volumn_discount[i],
            "Inner Dia D": inner_dia_d[i],
            "Outer Dia D": outer_dia_d[i],
            "Width B": width_b[i],
            "Basic Load Rating CR": basic_load_rating_cr[i],
            "Basic Load Rating COR": basic_load_rating_cor[i],
            "Weight": weight[i]
        })
    print("all_data:", all_data)
    # print("all_data:", all_data)
    driver.quit()

    # # Lưu ra Excel
    if all_data:
        df = pd.DataFrame(all_data)
        output_file = "misumi_bearings_4_col.xlsx"
        df.to_excel(output_file, index=False)
        print(f"✅ Đã lưu dữ liệu vào {output_file}")
    else:
        print("⚠ Không lấy được dữ liệu nào.")


if __name__ == "__main__":
    main()