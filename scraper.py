import time
import json
import pandas as pd
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager

# --- CONFIGURATION ---
BASE_URL = "https://www.myscheme.gov.in/search"
OUTPUT_FILE = "schemes_database.csv"
MAX_PAGES = 5  # Set a limit for testing (e.g., scrape first 5 pages)

def setup_driver():
    """Sets up the Chrome Browser in 'Headless' mode."""
    chrome_options = Options()
    # chrome_options.add_argument("--headless")  # Keep commented to SEE the browser working
    chrome_options.add_argument("--disable-gpu")
    chrome_options.add_argument("--window-size=1920,1080")
    chrome_options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/90.0.4430.212 Safari/537.36")
    
    service = Service(ChromeDriverManager().install())
    driver = webdriver.Chrome(service=service, options=chrome_options)
    return driver

def scrape_schemes():
    driver = setup_driver()
    all_schemes = []
    page_count = 1
    
    print(f"[*] Connecting to {BASE_URL}...")
    driver.get(BASE_URL)
    time.sleep(5) # Initial wait for site to load

    try:
        while page_count <= MAX_PAGES:
            print(f"--- Scraping Page {page_count} ---")
            
            # 1. Wait for cards to be visible
            wait = WebDriverWait(driver, 10)
            # This XPATH looks for the card container common on myscheme
            # Note: Selectors can change. If this fails, inspect the site for the card class.
            cards = driver.find_elements(By.XPATH, "//div[contains(@class, 'p-4') or contains(@class, 'shadow')]//h2")
            
            if not cards:
                print("[!] No cards found on this page. Stopping.")
                break

            # 2. Extract Data from current page
            for card in cards:
                try:
                    title = card.text
                    if not title: continue
                    
                    # Try to capture the summary text below the title
                    parent = card.find_element(By.XPATH, "./..")
                    raw_text = parent.text.replace("\n", " | ")
                    
                    scheme_obj = {
                        "title": title,
                        "description": raw_text[:200], # First 200 chars
                        "industry": "General", # Default, we will improve classification later
                        "link": BASE_URL
                    }
                    all_schemes.append(scheme_obj)
                    print(f"   -> Found: {title[:40]}...")
                except:
                    continue

            # 3. PAGINATION LOGIC (The New Part)
            try:
                # Look for the 'Right Arrow' or 'Next' button
                # This XPATH looks for a button that likely goes to the next page
                next_btn = driver.find_element(By.XPATH, "//button[@aria-label='Go to next page'] | //li[@title='Next Page']//button | //button[contains(., 'Next')]")
                
                # Check if button is disabled (last page)
                if not next_btn.is_enabled():
                    print("[*] Next button is disabled. Reached end.")
                    break
                
                # Click using JavaScript (More robust than standard .click())
                driver.execute_script("arguments[0].click();", next_btn)
                print("[*] Clicking Next...")
                
                page_count += 1
                time.sleep(5) # Wait for new page to load
                
            except Exception as e:
                print(f"[*] Could not find Next button or reached end: {e}")
                break
                
    except Exception as e:
        print(f"[!] Critical Error: {e}")
        
    finally:
        driver.quit()
        return all_schemes

if __name__ == "__main__":
    print("--- STARTING YOJNA BOT SCRAPER ---")
    data = scrape_schemes()
    
    if data:
        # Save directly to CSV for the Bot to use
        df = pd.DataFrame(data)
        df.to_csv(OUTPUT_FILE, index=False)
        print(f"\n[SUCCESS] Scraped {len(data)} schemes.")
        print(f"Data saved to '{OUTPUT_FILE}'")
    else:
        print("\n[FAILED] No data found.")