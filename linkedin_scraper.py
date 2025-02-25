import os
import time
import sqlite3
import undetected_chromedriver as uc
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from dotenv import load_dotenv
from bs4 import BeautifulSoup

print("Loading environment variables...")
load_dotenv()
EMAIL = os.getenv("LINKEDIN_EMAIL")
PASSWORD = os.getenv("LINKEDIN_PASSWORD")

# Set up Selenium WebDriver with undetected_chromedriver
print("Setting up WebDriver...")
options = uc.ChromeOptions()
options.add_argument("--headless")  
options.add_argument("--disable-gpu")
options.add_argument("--disable-blink-features=AutomationControlled")
options.add_argument("--no-sandbox")
options.add_argument("--disable-dev-shm-usage")


print("Initializing WebDriver...")
driver = uc.Chrome(options=options)

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

# Verify login success
print("Verifying login...")
print("Current Page Title:", driver.title)
if "LinkedIn Login" in driver.title:
    print("Login failed. Check your credentials.")
    driver.quit()
    exit()
print("Login successful!")

# Navigate to IT Expert
print("Searching for IT Experts...")
search_url = "https://www.linkedin.com/search/results/people/?keywords=IT%20Expert"
driver.get(search_url)
time.sleep(5)

# Extract profile URLs using XPath
print("Extracting profile URLs...")
profile_links = driver.find_elements(By.XPATH, "//a[contains(@href, '/in/')]")
profile_urls = [link.get_attribute("href") for link in profile_links]

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
    job_title = soup.find("div", {"class": "text-body-medium"})

    name_text = name.text.strip() if name else "N/A"
    job_text = job_title.text.strip() if job_title else "N/A"

    print(f"Name: {name_text}, Job Title: {job_text}")
    data.append((name_text, job_text, profile_url))

driver.quit()


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
