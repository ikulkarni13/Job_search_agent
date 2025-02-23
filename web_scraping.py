import pandas as pd
import numpy as np
from serpapi import GoogleSearch
import requests
import time
import os
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.common.exceptions import NoSuchElementException
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

linkedin_email = os.environ.get('linkedin_email')
linkedin_password = os.environ.get('linkedin_password')

driver = webdriver.Chrome()
driver.get("https://www.linkedin.com/login")
time.sleep(2)

username_box = driver.find_element(By.ID, "username")
password_box = driver.find_element(By.ID, "password")

username_box.send_keys(linkedin_email)
password_box.send_keys(linkedin_password)
sign_in_button = driver.find_element(By.XPATH, "//button[@type='submit']")
sign_in_button.click()

time.sleep(2)

#Linkedin-jobs
url = r'https://www.linkedin.com/jobs/search/?f_WT=1%2C2%2C3&geoId=105080838&keywords=software%20engineer&origin=JOB_SEARCH_PAGE_JOB_FILTER'
driver.get(url)
time.sleep(2) 


xpaths = {
 'Role'      :".//a[contains(@class, 'job-card-list__title--link')]/span[1]/strong",
 'Company'   :".//div[contains(@class, 'artdeco-entity-lockup__subtitle ember-view')]",
 'Location'  :".//div[contains(@class, 'rtdeco-entity-lockup__caption ember-view')]/ul[1]/li[1]/span",
 'Salary'    :".//div[contains(@class, 'mt1 t-sans t-12 t-black--light t-normal t-roman artdeco-entity-lockup__metadata ember-view')]/ul[1]/li[1]/span",
 'Link'      :".//a[contains(@class, 'job-card-list__title--link')]"
}

data = {key:[] for key in xpaths}
scrollable_div = driver.find_element(By.XPATH, "//div[contains(@class, 'scaffold-layout__list ')]/div[1]") 


def scrape_jobs_on_page(driver, scrollable_div, xpaths, data, processed_cards):
    attempts = 0
    max_attempts = 3
    last_height = 0
    consecutive_same_count = 0
    max_same_count = 2

    while attempts < max_attempts:
        job_cards = driver.find_elements(By.XPATH, "//div[contains(@class, 'flex-grow-1 artdeco-entity-lockup__content ember-view')]")
        
        for card in job_cards:
            card_id = card.get_attribute("id")
            
            if card_id not in processed_cards:
                try:
                    driver.execute_script('arguments[0].scrollIntoView({block: "center", behavior: "smooth"});', card)
                    time.sleep(1)
                
                # Extract data
                    try:
                        role = card.find_element(By.XPATH, xpaths['Role']).text.strip()
                    except Exception:
                        print("Could not find role for card")
                        role = "*missing data*"

                    try:
                        company = card.find_element(By.XPATH, xpaths['Company']).text.strip()
                    except Exception:
                        print("Could not find company for card")
                        company = "*missing data*"

                    try:
                        location = card.find_element(By.XPATH, xpaths['Location']).text.strip()
                    except Exception:
                        print("Could not find location for card")
                        location = "*missing data*"

                    try:
                        salary = card.find_element(By.XPATH, xpaths['Salary']).text.strip()
                    except Exception:
                        print("Could not find salary for card")
                        salary = "*missing data*"

                    try:
                        link = card.find_element(By.XPATH, xpaths['Link']).get_attribute('href')
                    except Exception:
                        print("Could not find link for card")
                        link = "*missing data*"

                    # Store the data
                    data['Role'].append(role)
                    data['Company'].append(company)
                    data['Location'].append(location)
                    data['Salary'].append(salary)
                    data['Link'].append(link)
                    
                    processed_cards.add(card_id)
                    print(f"Processed {len(processed_cards)} jobs")
                
                except Exception as e:
                    print(f"Error processing card: {e}")
    
        new_height = driver.execute_script("return arguments[0].scrollHeight", scrollable_div)
        if new_height == last_height:
            attempts += 1
            consecutive_same_count += 1
        else:
            last_height = new_height
            attempts = 0
            consecutive_same_count = 0
        
        if consecutive_same_count >= max_same_count:
            break
    
        driver.execute_script("arguments[0].scrollTop += 300;", scrollable_div)
        time.sleep(1)


def scrape_multiple_pages(max_pages):
    all_data = {key:[] for key in xpaths}
    processed_cards = set()
    current_page = 1

    while current_page <= max_pages:
        print(f"\nScraping page {current_page}")
        
        # Scrape current page
        scrollable_div = driver.find_element(By.XPATH, "//div[contains(@class, 'scaffold-layout__list ')]/div[1]")
        scrape_jobs_on_page(driver, scrollable_div, xpaths, all_data, processed_cards)
        
        # Try to go to next page
        try:
            next_button = driver.find_element(By.XPATH, f"//button[@aria-label='Page {current_page + 1}']")
            driver.execute_script("arguments[0].click();", next_button)
            time.sleep(3)  # Wait for new page to load
            current_page += 1
        except NoSuchElementException:
            print(f"No more pages available after page {current_page}")
            break
    
    return all_data

max_pages = 2 
data = scrape_multiple_pages(max_pages)
print(f"Total jobs collected: {len(data['Role'])}")

# Create DataFrame and save to CSV
df = pd.DataFrame(data)
df.to_csv(r'C:\Users\iraku\OneDrive\Desktop\AI_Agent\Linkedin_Jobs.csv', index=False)