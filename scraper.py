import os
import time
import pickle
import sqlite3
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.firefox.service import Service as FirefoxService
from webdriver_manager.firefox import GeckoDriverManager
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from dotenv import load_dotenv
from bs4 import BeautifulSoup

print("Loading environment variables...")
load_dotenv()
EMAIL = os.getenv("LINKEDIN_EMAIL")
PASSWORD = os.getenv("LINKEDIN_PASSWORD")

# Set up Selenium WebDriver with Firefox
print("Setting up WebDriver...")
options = webdriver.FirefoxOptions()
# options.add_argument("--headless")  # Disable headless mode for debugging
options.add_argument("--disable-gpu")
options.add_argument("--no-sandbox")
options.add_argument("--disable-dev-shm-usage")

print("Initializing WebDriver...")
driver = webdriver.Firefox(service=FirefoxService(GeckoDriverManager().install()), options=options)

# Load cookies if available
cookies_file = "linkedin_cookies.pkl"
if os.path.exists(cookies_file):
    driver.get("https://www.linkedin.com")
    for cookie in pickle.load(open(cookies_file, "rb")):
        driver.add_cookie(cookie)
    print("Cookies loaded. Skipping login.")
else:
    driver.get("https://www.linkedin.com/login")
    time.sleep(3)
    
    # Log in
    print("Logging into LinkedIn...")
    email_input = driver.find_element(By.ID, "username")
    password_input = driver.find_element(By.ID, "password")
    email_input.send_keys(EMAIL)
    password_input.send_keys(PASSWORD)
    password_input.send_keys(Keys.RETURN)
    
    time.sleep(5)  # Allow time for login
    
    # Save cookies after successful login
    pickle.dump(driver.get_cookies(), open(cookies_file, "wb"))
    print("Cookies saved.")

# Verify login success
print("Verifying login...")
print("Current Page Title:", driver.title)
if "Security Verification" in driver.title or "Login" in driver.title:
    input("Complete CAPTCHA manually in the browser, then press Enter to continue...")
    print("Resuming after manual verification.")
    driver.refresh()

time.sleep(5)
print("Login successful!")

# Navigate to IT Expert
print("Searching for IT Experts...")
search_url = "https://www.linkedin.com/search/results/people/?keywords=IT%20Expert"
driver.get(search_url)
time.sleep(5)

# Scroll down to load more profiles
def scroll_page():
    last_height = driver.execute_script("return document.body.scrollHeight")
    for _ in range(5):  # Scroll multiple times
        driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
        time.sleep(3)
        new_height = driver.execute_script("return document.body.scrollHeight")
        if new_height == last_height:
            break
        last_height = new_height

scroll_page()

# Extract profile URLs using XPath
print("Extracting profile URLs...")
try:
    WebDriverWait(driver, 10).until(
        EC.presence_of_element_located((By.XPATH, "//a[contains(@href, '/in/')]") )
    )
    profile_links = driver.find_elements(By.XPATH, "//a[contains(@href, '/in/')]")
    profile_urls = list(set([link.get_attribute("href") for link in profile_links]))  # Remove duplicates
except:
    print("No profiles found. Exiting.")
    driver.quit()
    exit()

print("Extracted Profiles:")
for url in profile_urls:
    print(url)

data = []

# Scrape name and job title from profiles using Selenium
print("Scraping profile details...")
for profile_url in profile_urls[:5]:  # Limit to 5 profiles for testing
    driver.get(profile_url)
    time.sleep(5)  # Allow profile page to load

    soup = BeautifulSoup(driver.page_source, "html.parser")

    name = soup.find("h1")
    job_title = soup.find("div", class_="text-body-medium")

    name_text = name.text.strip() if name else "N/A"
    job_text = job_title.text.strip() if job_title else "N/A"

    print(f"Name: {name_text}, Job Title: {job_text}")
    if name_text != "N/A" and job_text != "N/A":
        data.append((name_text, job_text, profile_url))

driver.quit()

if not data:
    print("No valid data scraped. Exiting.")
    exit()

print("Storing data in database...")
conn = sqlite3.connect("linkedin_profiles.db")
cursor = conn.cursor()
cursor.execute("""
    CREATE TABLE IF NOT EXISTS profiles (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT,
        job_title TEXT,
        profile_url TEXT
    )
""")
cursor.executemany("INSERT INTO profiles (name, job_title, profile_url) VALUES (?, ?, ?)", data)
conn.commit()
conn.close()

print("Data successfully stored in the database.")
