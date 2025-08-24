import time
import pandas as pd
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager


# ====== HÀM LẤY DANH SÁCH PART NUMBER ======
def extract_all_part_numbers(driver):
    wait = WebDriverWait(driver, 60)
    time.sleep(5)
    #scroll xuống
    driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
    time.sleep(5)

    # Chờ đúng nút có id 'codeList'
    dropdown_btn = wait.until(EC.element_to_be_clickable((By.XPATH, "//*[@id='codeList']")))
    time.sleep(5)
    dropdown_btn.click()
    time.sleep(5)

    # Lấy tất cả option part number
    # Lấy tất cả các part number trong table tại xpath //*[@id="partNumberListTable"]/div/div[1]/table
    table = wait.until(EC.presence_of_element_located(
        (By.XPATH, "//*[@id='partNumberListTable']/div/div[1]/table"))
    )
    # Lấy tất cả các hàng trong tbody (bỏ qua header)
    rows = table.find_elements(By.CSS_SELECTOR, "tbody tr")
    part_numbers = []
    for row in rows:
        # Giả sử part number nằm ở cột đầu tiên (td đầu tiên)
        cells = row.find_elements(By.TAG_NAME, "td")
        if cells:
            part_number = cells[0].text.strip()
            if part_number:
                part_numbers.append(part_number)
    print("part_numbers:", part_numbers)
    print("part_numbers length:", len(part_numbers))

    return part_numbers


# ====== HÀM LẤY THÔNG SỐ MỖI PART (có retry) ======
def extract_specifications(driver, part_number, max_retry=3):
    wait = WebDriverWait(driver, 60)

    for attempt in range(1, max_retry + 1):
        try:
            # Mở dropdown
            dropdown_btn = wait.until(EC.element_to_be_clickable(
                (By.XPATH, "//div[contains(@class,'PartNumberDropDownList_partNumberSelection')]"))
            )
            dropdown_btn.click()
            time.sleep(3)

            # Click vào part_number tương ứng
            option = wait.until(EC.element_to_be_clickable(
                (By.XPATH, f"//div[@class='PartNumberDropDownList_partNumberOption__KnDz0' and @title='{part_number}']"))
            )
            option.click()
            time.sleep(6)

            # Lấy bảng thông số
            spec_table = wait.until(EC.presence_of_element_located(
                (By.CSS_SELECTOR, "div.SpecTable_tableWrapper__TkrZl"))
            )

            rows = spec_table.find_elements(By.CSS_SELECTOR, "tr")
            spec_data = {"Part Number": part_number}

            for row in rows:
                try:
                    cols = row.find_elements(By.CSS_SELECTOR, "td")
                    if len(cols) >= 2:
                        key = cols[0].text.strip()
                        value = cols[1].text.strip()
                        spec_data[key] = value
                except:
                    continue

            # Lấy giá
            try:
                price_elem = driver.find_element(By.CSS_SELECTOR, "span.product_price span")
                spec_data["Price"] = price_elem.text.strip()
            except:
                spec_data["Price"] = ""

            return spec_data

        except Exception as e:
            print(f"⚠️ Thử lần {attempt} cho {part_number} thất bại: {e}")
            if attempt < max_retry:
                print("⏳ Thử lại...")
                time.sleep(5)
            else:
                print(f"❌ Bỏ qua {part_number} sau {max_retry} lần thử.")
                return {"Part Number": part_number, "Error": str(e)}


# ====== MAIN ======
def main():
    url = "https://vn.misumi-ec.com/vona2/detail/110310367019/?KWSearch=bearing&searchFlow=results2products&list=PageSearchResult"

    # Khởi tạo Chrome
    service = Service(ChromeDriverManager().install())
    driver = webdriver.Chrome(service=service)
    driver.maximize_window()
    driver.get(url)

    print("Đang lấy danh sách Part Numbers...")
    part_numbers = extract_all_part_numbers(driver)
    print(f"Tìm thấy {len(part_numbers)} part numbers.")

    all_data = []
    for idx, pn in enumerate(part_numbers, start=1):
        print(f"({idx}/{len(part_numbers)}) Đang lấy dữ liệu: {pn}")
        data = extract_specifications(driver, pn, max_retry=3)
        all_data.append(data)

    driver.quit()

    # Lưu ra Excel
    if all_data:
        df = pd.DataFrame(all_data)
        output_file = "misumi_bearings.xlsx"
        df.to_excel(output_file, index=False)
        print(f"✅ Đã lưu dữ liệu vào {output_file}")
    else:
        print("⚠ Không lấy được dữ liệu nào.")


if __name__ == "__main__":
    main()