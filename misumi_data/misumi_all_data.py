import time
import pandas as pd
import os
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
from bs4 import BeautifulSoup
import time

def create_english_profile():
    """Create a persistent Chrome profile directory for English language"""
    profile_dir = os.path.join(os.getcwd(), "chrome_english_profile")
    if not os.path.exists(profile_dir):
        os.makedirs(profile_dir)
        print(f"✅ Created English profile directory: {profile_dir}")
    else:
        print(f"✅ Using existing English profile directory: {profile_dir}")
    return profile_dir

def setup_driver():
    chrome_options = Options()
    
    # Create and use persistent English profile
    profile_dir = create_english_profile()
    chrome_options.add_argument(f"--user-data-dir={profile_dir}")
    chrome_options.add_argument("--profile-directory=Default")
    
    # chrome_options.add_argument("--headless")  # Uncomment for headless mode
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    chrome_options.add_argument("--disable-gpu")
    chrome_options.add_argument("--window-size=1920,1080")
    
    # Force English language settings
    chrome_options.add_argument("--lang=en-US")
    chrome_options.add_argument("--accept-lang=en-US,en;q=0.9")
    chrome_options.add_argument("--accept-languages=en-US,en")
    chrome_options.add_argument("--lang=en")
    chrome_options.add_argument("--accept-language=en-US,en;q=0.9")
    
    # Set user agent with English locale
    chrome_options.add_argument("--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36")
    
    # Comprehensive language preferences
    chrome_options.add_experimental_option("prefs", {
        "intl.accept_languages": "en-US,en",
        "intl.locale_requested": "en-US",
        "intl.locale_override": "en-US",
        "profile.default_content_setting_values.notifications": 2,
        "profile.managed_default_content_settings.images": 1,
        "profile.default_content_setting_values.media_stream": 2,
        "translate": {"enabled": False},
        "translate_whitelists": {},
        "translate_blocked_languages": ["vi", "ja", "ko", "zh", "fr", "de", "es", "it", "pt", "ru", "ar"],
        "profile.content_settings.exceptions.translate": {
            "*,*": {
                "setting": 2
            }
        }
    })
    
    # Disable translation features
    chrome_options.add_argument("--disable-translate")
    chrome_options.add_argument("--disable-translate-script-url")
    chrome_options.add_argument("--disable-translate-new-ux")
    chrome_options.add_argument("--disable-features=TranslateUI")
    
    # Anti-detection settings
    chrome_options.add_argument("--disable-blink-features=AutomationControlled")
    chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
    chrome_options.add_experimental_option('useAutomationExtension', False)
    try:
        driver = webdriver.Chrome(options=chrome_options)
        driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
        # Set comprehensive HTTP headers for English
        driver.execute_cdp_cmd('Network.setExtraHTTPHeaders', {
            'headers': {
                'Accept-Language': 'en-US,en;q=0.9,en;q=0.8',
                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
                'Accept-Encoding': 'gzip, deflate, br',
                'Cache-Control': 'no-cache',
                'Accept-Lang': 'en-US,en;q=0.9',
                'X-Requested-With': 'XMLHttpRequest'
            }
        })
        
        # Force English locale and language
        driver.execute_cdp_cmd('Emulation.setLocaleOverride', {'locale': 'en-US'})
        driver.execute_cdp_cmd('Emulation.setGeolocationOverride', {
            'latitude': 40.7128,
            'longitude': -74.0060,
            'accuracy': 100
        })
        driver.execute_cdp_cmd('Page.setBypassCSP', {'enabled': True})
        
        # Set timezone to US Eastern
        driver.execute_cdp_cmd('Emulation.setTimezoneOverride', {'timezoneId': 'America/New_York'})
        
        # Additional language enforcement
        driver.execute_script("""
            // Override navigator language properties
            Object.defineProperty(navigator, 'language', {
                get: function() { return 'en-US'; }
            });
            Object.defineProperty(navigator, 'languages', {
                get: function() { return ['en-US', 'en']; }
            });
            Object.defineProperty(navigator, 'userLanguage', {
                get: function() { return 'en-US'; }
            });
            Object.defineProperty(navigator, 'browserLanguage', {
                get: function() { return 'en-US'; }
            });
            Object.defineProperty(navigator, 'systemLanguage', {
                get: function() { return 'en-US'; }
            });
            
            // Set document language
            if (document.documentElement) {
                document.documentElement.lang = 'en';
                document.documentElement.setAttribute('lang', 'en');
            }
            
            // Disable Google Translate
            if (window.google && window.google.translate) {
                window.google.translate.TranslateElement = function() {};
            }
        """)
        print("✅ Chrome driver đã được setup với tiếng Anh mặc định")
        print("✅ Headers và preferences đã được set để force tiếng Anh")
        try:
            language_check = driver.execute_script("return navigator.language || navigator.userLanguage || navigator.browserLanguage || navigator.systemLanguage;")
            print(f"✅ Browser language: {language_check}")
            languages_check = driver.execute_script("return navigator.languages;")
            print(f"✅ Browser languages: {languages_check}")
            doc_lang = driver.execute_script("return document.documentElement.lang;")
            print(f"✅ Document language: {doc_lang}")
        except Exception as e:
            print(f"⚠ Could not check browser language: {e}")
        return driver
    except Exception as e:
        print(f"Error setting up Chrome driver: {e}")
        return None

def enforce_english_language(driver):
    """Enforce English language on the current page"""
    try:
        # Set document language
        driver.execute_script("""
            if (document.documentElement) {
                document.documentElement.lang = 'en';
                document.documentElement.setAttribute('lang', 'en');
            }
            if (document.body) {
                document.body.lang = 'en';
                document.body.setAttribute('lang', 'en');
            }
            
            // Override navigator language properties
            Object.defineProperty(navigator, 'language', {
                get: function() { return 'en-US'; }
            });
            Object.defineProperty(navigator, 'languages', {
                get: function() { return ['en-US', 'en']; }
            });
            
            // Disable any translation popups
            const translateElements = document.querySelectorAll('[class*="translate"], [id*="translate"], [class*="Translate"], [id*="Translate"]');
            translateElements.forEach(el => {
                el.style.display = 'none';
                el.remove();
            });
            
            // Remove Google Translate iframe
            const translateIframes = document.querySelectorAll('iframe[src*="translate.google.com"]');
            translateIframes.forEach(iframe => iframe.remove());
        """)
        
        # Set additional headers for this page
        driver.execute_cdp_cmd('Network.setExtraHTTPHeaders', {
            'headers': {
                'Accept-Language': 'en-US,en;q=0.9,en;q=0.8',
                'Accept-Lang': 'en-US,en;q=0.9'
            }
        })
        
        print("✅ English language enforced on current page")
        return True
    except Exception as e:
        print(f"⚠ Could not enforce English language: {e}")
        return False

def get_other_data(driver):
    wait = WebDriverWait(driver, 60)
    time.sleep(10)
    driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
    time.sleep(3)
    driver.execute_script("window.scrollTo(0, 0);")
    time.sleep(3)

    spec_data = {}

    # Tìm tên sản phẩm
    product_name = "N/A"
    try:
        product_name_elem = driver.find_element(By.XPATH, "//*[@id='heading-description']/div")
        product_name = product_name_elem.text.strip()
    except Exception:
        pass

    # Lấy URL hình sản phẩm
    url_image = "N/A"
    try:
        image_elem = driver.find_element(By.XPATH, '//*[@id="actionsPanel"]/div[1]/div/img')
        url_image = image_elem.get_attribute("src") if image_elem else "N/A"
    except Exception:
        pass

    # Lấy URL hình Dimensional Drawing sử dụng full XPath được cung cấp
    dimensional_drawing_url = "N/A"
    try:
        drawing_img = None
        try:
            drawing_img = driver.find_element(
                By.XPATH,
                '/html/body/div[1]/div[2]/div/div/div/div[3]/div[2]/div[3]/div[2]/div/div[1]/div/div[4]/img[1]'
            )
        except Exception:
            drawing_img = None
        if drawing_img:
            dimensional_drawing_url = drawing_img.get_attribute("src") or "N/A"
    except Exception:
        pass

    spec_data['Product Name'] = [product_name]
    spec_data['Product Image URL'] = [url_image]
    spec_data['Dimensional Drawing'] = [dimensional_drawing_url]

    try:
        spec_table = wait.until(EC.presence_of_element_located(
            (By.CLASS_NAME, "SpecTable_tableWrapper__J3sKG")
        ))
        spec_labels = spec_table.find_elements(By.CLASS_NAME, "SpecTable_specLabel__5D8Cy")
        spec_values = spec_table.find_elements(By.CLASS_NAME, "SpecTable_specValue__5D8Cy")
        for i, label_elem in enumerate(spec_labels):
            try:
                label_text = label_elem.text.strip()
                if label_text:
                    value_text = "N/A"
                    if i < len(spec_values):
                        try:
                            value_elem = spec_values[i]
                            if value_elem and value_elem.text:
                                value_text = value_elem.text.strip()
                                if not value_text:
                                    value_text = "N/A"
                        except Exception:
                            value_text = "N/A"
                    spec_data[label_text] = [value_text]
            except Exception:
                continue
    except Exception:
        try:
            spec_table = wait.until(EC.presence_of_element_located(
                (By.CSS_SELECTOR, "[class*='SpecTable'][class*='tableWrapper']")
            ))
            spec_labels = spec_table.find_elements(By.CSS_SELECTOR, "[class*='specLabel']")
            spec_values = spec_table.find_elements(By.CSS_SELECTOR, "[class*='specValue']")
            for i, label_elem in enumerate(spec_labels):
                try:
                    label_text = label_elem.text.strip()
                    if label_text:
                        value_text = "N/A"
                        if i < len(spec_values):
                            try:
                                value_elem = spec_values[i]
                                if value_elem and value_elem.text:
                                    value_text = value_elem.text.strip()
                                    if not value_text:
                                        value_text = "N/A"
                            except Exception:
                                value_text = "N/A"
                        spec_data[label_text] = [value_text]
                except Exception:
                    continue
        except Exception:
            pass
    try:
        # Wait for the catalog link to be present and click it
        catalog_link = wait.until(EC.presence_of_element_located(
            (By.CSS_SELECTOR, "a[data-testid='catalog']")
        ))
        catalog_link.click()
        
        # Wait for 5 seconds to ensure the catalog content loads
        time.sleep(5)
        
        # Locate the image within the catalog container
        catalog_container = wait.until(EC.presence_of_element_located(
            (By.CSS_SELECTOR, "div.catalogContainer.CatalogViewer_container__wzYZ8")
        ))
        img_element = catalog_container.find_element(By.TAG_NAME, "img")
        img_src = img_element.get_attribute("src")
        
        # Store the image link in the spec_data
        spec_data['Catalog Image'] = [img_src]
        
        print(f"✅ Catalog image link extracted: {img_src}")
    except Exception as e:
        print(f"⚠ Error extracting catalog image: {e}")
    return spec_data

def get_url_From_file(file_path, start_index, end_index):
    try:
        df = pd.read_csv(file_path)
        if 'Product URL' in df.columns:
            urls = df['Product URL'].tolist()
            if start_index < 0:
                start_index = 0
            if end_index > len(urls):
                end_index = len(urls)
            if start_index >= end_index:
                print("⚠ Invalid index range: start_index >= end_index")
                return []
            return urls[start_index:end_index]
        else:
            print("⚠ 'Product URL' column not found in the CSV file.")
            print(f"Available columns: {list(df.columns)}")
            return []
    except FileNotFoundError:
        print(f"⚠ File not found: {file_path}")
        return []
    except Exception as e:
        print(f"⚠ Error reading file {file_path}: {e}")
        return []

def get_data_from_url(driver, url):
    try:
        try:
            driver.get(url)
            time.sleep(5)
            print(f"✅ Loaded URL: {driver.current_url}")
            
            # Enforce English language immediately after page load
            print("🔧 Enforcing English language on page...")
            enforce_english_language(driver)
            time.sleep(2)
            
            try:
                page_language = driver.execute_script("return navigator.language || navigator.userLanguage;")
                print(f"✅ Page language: {page_language}")
                doc_lang = driver.execute_script("return document.documentElement.lang;")
                print(f"✅ Document language: {doc_lang}")
                
                # Verify English is set
                if doc_lang and doc_lang != 'en' and doc_lang != 'en-US':
                    print(f"⚠ Document language is still {doc_lang}, forcing English...")
                    driver.execute_script("document.documentElement.lang = 'en'; document.documentElement.setAttribute('lang', 'en');")
            except Exception as e:
                print(f"⚠ Could not check page language: {e}")
        except Exception as e:
            print(f"❌ ERROR: Không thể load URL: {e}")
            return {}
        english_clicked = False
        try:
            time.sleep(2)
            english_indicators = [
                "//span[contains(text(), 'Specifications')]",
                "//div[contains(text(), 'Basic')]",
                "//h1[contains(text(), 'Product')]",
                "div[contains(text(), 'Part Number')]",
                "//div[contains(text(), 'Specifications')]",
                "//span[contains(text(), 'Product')]"
            ]
            english_found = False
            for indicator in english_indicators:
                try:
                    elem = driver.find_element(By.XPATH, indicator)
                    if elem and elem.is_displayed():
                        print(f"✅ English detected: Found '{elem.text}'")
                        english_found = True
                        break
                except:
                    continue
            if english_found:
                print("✅ Trang đã tự động ở tiếng Anh nhờ Chrome options!")
                english_clicked = True
            else:
                print("⚠ Trang chưa ở tiếng Anh, cần click nút English...")
        except Exception as e:
            print(f"⚠ Could not check page language: {e}")
            print("⚠ Proceeding with manual language switch...")
        try:
            print("Debug: Tìm tất cả các link trên trang...")
            all_page_links = driver.find_elements(By.TAG_NAME, "a")
            print(f"Found {len(all_page_links)} total links on page")
            for i, link in enumerate(all_page_links[:10]):
                try:
                    link_text = link.text.strip()
                    link_class = link.get_attribute("class")
                    link_lang = link.get_attribute("lang")
                    print(f"  Link {i+1}: Text='{link_text}', Class='{link_class}', Lang='{link_lang}'")
                except:
                    print(f"  Link {i+1}: Error reading attributes")
            english_selectors = [
                "//a[contains(text(), 'English')]",
                "//a[@lang='en']",
                "//a[contains(@class, 'language') and contains(text(), 'English')]",
                "//button[contains(text(), 'English')]",
                "//div[contains(@class, 'language')]//a[contains(text(), 'English')]",
                "//a[contains(@class, 'Anchor_anchorLink') and contains(text(), 'English')]",
                "//a[contains(@class, 'SwitchLanguage') and contains(text(), 'English')]"
            ]
            for i, selector in enumerate(english_selectors):
                try:
                    print(f"Trying English selector {i+1}: {selector}")
                    english_btn = driver.find_element(By.XPATH, selector)
                    if english_btn and english_btn.is_displayed():
                        print(f"Found English button, clicking...")
                        driver.execute_script("arguments[0].scrollIntoView(true);", english_btn)
                        time.sleep(2)
                        english_btn.click()
                        time.sleep(5)
                        print("Clicked English button")
                        english_clicked = True
                        break
                except Exception as e:
                    print(f"Selector {i+1} failed: {e}")
                    continue
            if not english_clicked:
                print("Trying to find English link by text...")
                all_links = driver.find_elements(By.TAG_NAME, "a")
                for link in all_links:
                    try:
                        link_text = link.text.strip()
                        if 'English' in link_text or 'EN' in link_text:
                            print(f"Found English link: '{link_text}'")
                            if link.is_displayed():
                                driver.execute_script("arguments[0].scrollIntoView(true);", link)
                                time.sleep(1)
                                link.click()
                                time.sleep(5)
                                print("Clicked English link")
                                english_clicked = True
                                break
                    except Exception as e:
                        continue
            if not english_clicked:
                print("Trying to find English button by special attributes...")
                try:
                    english_btn = driver.find_element(By.XPATH, "//*[@data-testid='language-option-en']")
                    if english_btn and english_btn.is_displayed():
                        english_btn.click()
                        time.sleep(5)
                        print("Clicked English button by data-testid")
                        english_clicked = True
                except:
                    try:
                        english_btn = driver.find_element(By.XPATH, "//a[contains(@class, 'SwitchLanguage_selected__bD2Op')]")
                        if english_btn and english_btn.is_displayed():
                            english_btn.click()
                            time.sleep(5)
                            print("Clicked English button by special class")
                            english_clicked = True
                    except Exception as e:
                        print(f"Special class method failed: {e}")
            if not english_clicked:
                print("Trying to find English button by exact text...")
                try:
                    english_elements = driver.find_elements(By.XPATH, "//*[contains(translate(text(), 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), 'english')]")
                    for elem in english_elements:
                        try:
                            if elem.is_displayed() and elem.is_enabled():
                                print(f"Found English element: '{elem.text}'")
                                elem.click()
                                time.sleep(5)
                                print("Clicked English element by text search")
                                english_clicked = True
                                break
                        except:
                            continue
                except Exception as e:
                    print(f"Text search method failed: {e}")
        except Exception as e:
            print(f"Error during language switching: {e}")
        if english_clicked:
            print("✅ Successfully switched to English language")
            time.sleep(3)
        else:
            print("⚠ Không thể click nút English, kiểm tra xem trang đã ở tiếng Anh chưa...")
            try:
                time.sleep(2)
                english_indicators = [
                    "//span[contains(text(), 'Specifications')]",
                    "//div[contains(text(), 'Basic')]",
                    "//h1[contains(text(), 'Product')]",
                    "//div[contains(text(), 'Part Number')]",
                    "//div[contains(text(), 'Specifications')]",
                    "//span[contains(text(), 'Product')]"
                ]
                english_found = False
                for indicator in english_indicators:
                    try:
                        elem = driver.find_element(By.XPATH, indicator)
                        if elem and elem.is_displayed():
                            english_found = True
                            break
                    except:
                        continue
                if english_found:
                    english_clicked = True
            except Exception:
                pass
        if not english_clicked:
            return {}
        time.sleep(2)
        spec_data = get_other_data(driver)
        return spec_data
    except Exception as e:
        print(f"Error in get_data_from_url: {e}")
        return {}

def validate_data_consistency(all_combined_data):
    if not all_combined_data:
        return False
    lengths = [len(values) for values in all_combined_data.values()]
    if len(set(lengths)) != 1:
        print(f"⚠ Lỗi: Các cột có độ dài khác nhau: {lengths}")
        return False
    print(f"✅ Tất cả {len(all_combined_data)} cột đều có {lengths[0]} rows")
    return True

def verify_english_setup(driver):
    """Verify that English language setup is working correctly"""
    try:
        print("🔍 Verifying English language setup...")
        
        # Check navigator properties
        nav_lang = driver.execute_script("return navigator.language;")
        nav_langs = driver.execute_script("return navigator.languages;")
        
        # Check document properties
        doc_lang = driver.execute_script("return document.documentElement.lang;")
        
        # Check if translation is disabled
        translate_disabled = driver.execute_script("""
            return !window.google || !window.google.translate || 
                   document.querySelectorAll('[class*="translate"], [id*="translate"]').length === 0;
        """)
        
        print(f"✅ Navigator language: {nav_lang}")
        print(f"✅ Navigator languages: {nav_langs}")
        print(f"✅ Document language: {doc_lang}")
        print(f"✅ Translation disabled: {translate_disabled}")
        
        if nav_lang == 'en-US' and doc_lang == 'en' and translate_disabled:
            print("🎉 English language setup verified successfully!")
            return True
        else:
            print("⚠ English language setup needs adjustment")
            return False
            
    except Exception as e:
        print(f"⚠ Could not verify English setup: {e}")
        return False

def main():
    print("🚀 Starting web scraping with English language enforcement...")
    path=r"C:\Users\Admin\Music\Python\Chay-Code\misumi_data"
    start=0
    end=284
    urls = get_url_From_file(r"C:\Users\Admin\Music\Python\Chay-Code\misumi_data\same_day_products_from_html_misumi.csv", start, end)
    name_file_to_save = r"C:\Users\Admin\Music\Python\Chay-Code\misumi_data\product_specifications_"+str(start)+"_"+str(end)
    all_combined_data = {}
    total_rows_processed = 0
    total_urls = len(urls)
    
    # Test English setup with first URL
    if urls:
        print("🧪 Testing English language setup with first URL...")
        test_driver = setup_driver()
        if test_driver:
            try:
                test_driver.get("https://www.google.com")
                time.sleep(3)
                verify_english_setup(test_driver)
                test_driver.quit()
            except Exception as e:
                print(f"⚠ Test setup failed: {e}")
    
    for idx, url in enumerate(urls):
        print(f"=== Đang xử lý link thứ {idx+1}/{total_urls}: {url}")
        driver = setup_driver()
        if not driver:
            print("Failed to setup Chrome driver")
            continue
        try:
            driver.maximize_window()
            
            # Periodically re-enforce English language every 10 URLs
            if idx > 0 and idx % 10 == 0:
                print("🔄 Re-enforcing English language settings...")
                enforce_english_language(driver)
            
            url_data = get_data_from_url(driver, url)
            if not url_data:
                print(f"No data structure extracted from URL: {url}")
                continue
            url_row_count = 1
            if 'Source_URL' not in all_combined_data:
                all_combined_data['Source_URL'] = []
            all_combined_data['Source_URL'].append(url)
            new_columns = []
            for key in url_data.keys():
                if key not in all_combined_data:
                    new_columns.append(key)
                    all_combined_data[key] = []
                    all_combined_data[key].extend([''] * total_rows_processed)
            missing_columns = []
            for key in all_combined_data.keys():
                if key not in url_data and key != 'Source_URL':
                    missing_columns.append(key)
            for key in all_combined_data:
                while len(all_combined_data[key]) < total_rows_processed:
                    all_combined_data[key].append('')
            for key, values in url_data.items():
                all_combined_data[key].append(values[0] if values else '')
            for key in missing_columns:
                all_combined_data[key].append('')
            total_rows_processed += 1

            # In ra kết quả thu được từ link này
            print(f"Kết quả từ link {idx+1}/{total_urls}:")
            for k, v in url_data.items():
                print(f"  {k}: {v[0] if v else ''}")
            print("-" * 40)
        except Exception as e:
            print(f"Error processing URL {url}: {e}")
        finally:
            driver.quit()
    print(f"Total rows processed: {total_rows_processed}")
    print("Combined data keys:", list(all_combined_data.keys()))
    if not validate_data_consistency(all_combined_data):
        print("⚠ Dữ liệu không nhất quán, không thể lưu file")
        return
    if all_combined_data and total_rows_processed > 0:
        df = pd.DataFrame(all_combined_data)
        output_file = name_file_to_save + ".xlsx"
        df.to_excel(output_file, index=False)
        print(f"✅ Đã lưu dữ liệu vào {output_file}")
        print(f"DataFrame shape: {df.shape}")
        print("\nThống kê dữ liệu:")
        for col in df.columns:
            non_empty_count = (df[col] != '').sum()
            print(f"  {col}: {non_empty_count}/{len(df)} rows có dữ liệu")
    else:
        print("⚠ Không lấy được dữ liệu nào.")
    
    # Final English language setup summary
    print("\n" + "="*60)
    print("🎯 ENGLISH LANGUAGE SETUP SUMMARY")
    print("="*60)
    print("✅ Persistent Chrome profile created for English language")
    print("✅ All HTTP headers set to English")
    print("✅ Translation features disabled")
    print("✅ Navigator language properties overridden")
    print("✅ Document language enforced on every page")
    print("✅ Periodic language re-enforcement every 10 URLs")
    print("✅ US locale, timezone, and geolocation set")
    print("="*60)

if __name__ == "__main__":
    main()