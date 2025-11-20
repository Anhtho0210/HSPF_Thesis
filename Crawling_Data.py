from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException
import time
import logging
import datetime
import json 
from typing import List
import random

today = datetime.date.today().isoformat()

# --- Configuration for Limiting Programs ---
PROGRAM_LIMIT = 10
# --- End Configuration ---

logging.basicConfig(filename='./logs/log_'+str(today) +
                    '.txt', level=logging.DEBUG)

parent_url = "https://www2.daad.de/deutschland/studienangebote/international-programmes/en/result/?cert=&admReq=&langExamPC=&langExamLC=&langExamSC=&degree%5B%5D=2&fos%5B%5D=&langDeAvailable=&langEnAvailable=&lang%5B%5D=2&modStd%5B%5D=&cit%5B%5D=&tyi%5B%5D=&ins%5B%5D=&fee=&bgn%5B%5D=&dat%5B%5D=&prep_subj%5B%5D=&prep_degree%5B%5D=&sort=4&dur=&q=&limit=10&offset=&display=list&lvlEn%5B%5D=&subjectGroup%5B%5D=&subjects%5B%5D="
service = Service(ChromeDriverManager().install())
driver = webdriver.Chrome(service=service)
# Increased initial wait time for stability
wait = WebDriverWait(driver, 10) 
driver.get(parent_url)

# --- UPDATED PARAMETERS FOR JSON OUTPUT ---
params = [
    "program_id", "name", "institution", "city", "url",
    "tuition_fee","semester_fee", "start_date", "description", "admission_req",
    "language_req", "application_deadline","submit_to"
]
cols = params # Use the same for the column names/keys
# --- END UPDATED PARAMETERS ---

final_data = []

def fetch_links():
    """
    Fetches program detail URLs from the overview page, handling pagination 
    until the PROGRAM_LIMIT is reached or no more pages are available.
    """
    all_urls = []
    
    # 1. Ensure the driver is on the correct search results page
    # (Assuming apply_filters has been called and the page is loaded)
    
    print(f"Starting link retrieval, aiming for {PROGRAM_LIMIT} programs...")
    
    page_count = 1

    while True:
        try:
            print(f"Processing Page {page_count}. Total links found: {len(all_urls)}")
            
            # --- 1. Fetch links on the current page ---
            
            # Use the provided link selector (adjust if necessary, but this is functional)
            current_page_elements = wait.until(EC.presence_of_all_elements_located(
                (By.CSS_SELECTOR, ".list-inline-item.mr-0.js-course-detail-link")))
            
            current_page_links = [item.get_attribute("href") for item in current_page_elements]
            
            if not current_page_links:
                print("No links found on this page. Stopping pagination.")
                break
            
            # --- 2. Append links and check limit ---
            
            links_to_add = PROGRAM_LIMIT - len(all_urls)
            if links_to_add > 0:
                # Only add the necessary number of links to reach the limit
                all_urls.extend(current_page_links[:links_to_add])
            
            # Check if the limit has been reached after adding links
            if len(all_urls) >= PROGRAM_LIMIT:
                print(f"Reached the program limit of {PROGRAM_LIMIT}. Exiting loop.")
                break 
            
 # In fetch_links() function, inside the while loop, replace the old click block:

            # --- 3. Go to the next page (Revised Click Block) ---
            
            print("Attempting to click next page button with robust wait...")
            
            # 🌟 REVISED SELECTOR: Target the unique class and its 'href="#"' attribute 
            NEXT_BUTTON_SELECTOR = "a.js-result-pagination-next[href='#']"

            # 1. Wait until the button is clickable
            next_button = wait.until(
                EC.element_to_be_clickable((By.CSS_SELECTOR, NEXT_BUTTON_SELECTOR))
            )

            # 2. Check for disabled state (using the HTML snippet)
            # The HTML doesn't explicitly show a 'disabled' class, but let's check for visual readiness.
            
            # 3. Use JavaScript to click if Selenium's native click fails (the most reliable workaround for tricky AJAX buttons)
            try:
                # Attempt standard click first
                next_button.click()
            except Exception:
                # Fallback: Use JavaScript to force the click
                driver.execute_script("arguments[0].click();", next_button)
                
            print(f"Clicked 'Next' button via CSS: {NEXT_BUTTON_SELECTOR}")
            
            # Mandatory ethical delay after a click/request
            time.sleep(random.uniform(2, 5)) 
            
            # Wait for the content to change (ensure old links are gone)
            wait.until(EC.staleness_of(current_page_elements[0]))
            
            page_count += 1
            
        except TimeoutException:
            print("Pagination Timeout: Next button or new links did not appear in time. Assuming end of results.")
            break
        except Exception as e:
            # Catch any other failure during the click/wait process
            print(f"Critical error during pagination: {e}. Stopping link retrieval.")
            break
        
    return all_urls

def accept_cookies():
    try:
        print("Attempting to accept cookies...")
        # Use a longer wait (15s) specific to the cookie banner load
        cookie_wait = WebDriverWait(driver, 15)
        
        # FIX: The original selector "button.qa-cookie-consent-accept-selected" is correct.
        # We wrap it in a try/except to tolerate failure.
        cookie_button = cookie_wait.until(EC.element_to_be_clickable((
            By.CSS_SELECTOR, "button.qa-cookie-consent-accept-selected")))
        cookie_button.click()
        print("Cookies accepted.")
        time.sleep(1)
    except TimeoutException:
        print("Cookie banner did not appear or was not clickable within 15 seconds. Proceeding...")
    except NoSuchElementException as e:
        print(f"Cookie button selector failed: {e}. Proceeding...")
    except Exception as e:
        print(f"An unexpected error occurred during cookie acceptance: {e}")


def surf1():
    try:
        # accept cookies (now more robust)
        accept_cookies()

        # fetch links
        all_links = fetch_links()
        return all_links

    except Exception as e:
        print("CRITICAL error occured in surf1.... ", e)
        logging.critical(e, exc_info=True)
        # Always return an iterable on error to prevent 'NoneType' error in main
        return []


def textcombiner(targetIndex,tab_id):
    all_text = []
    try:
        # Re-using the original index-based selector for generic detail items
        reqs = wait.until(EC.presence_of_all_elements_located((
            By.CSS_SELECTOR, "#"+tab_id+" > .container > .c-description-list > *:nth-child("+targetIndex+") > *")))
        for p in reqs:
            all_text.append(p.get_attribute('innerText').strip())
        return "\n".join(all_text)
    except Exception as e:
        # print(f"Error in textcombiner for index {targetIndex}: {e}")
        return "N/A" 

def extract_dt_dd_by_label(label_text):
    """
    Helper function to extract the text from the <dd> element immediately
    following a <dt> element that contains the specified label text.
    Uses normalize-space() for robust text matching based on the DAAD HTML structure.
    """
    # Uses normalize-space() to ignore extra whitespace around the label text
    # This XPath pattern is reliable for the DAAD's <dt>/<dd> structure.
    xpath_selector = f"//dt[normalize-space(text()) = '{label_text}']" \
                     f"/following-sibling::dd[1]"
    try:
        # Use WebDriverWait to ensure the element is loaded before attempting to extract
        element = wait.until(EC.presence_of_element_located((
            By.XPATH, xpath_selector)))
        return element.get_attribute('innerText').strip()
    except Exception:
        # Return "N/A" if the element is not found within the timeout
        return "N/A"
    
def paramData(param, item_link):
    # This function extracts data for a single parameter
    try:
        # --- Common/Simple Parameters ---
        if (param == "name"):
            # h2.c-detail-header__title > span:nth-child(1)
            return wait.until(EC.presence_of_element_located((
                By.CSS_SELECTOR, "h2.c-detail-header__title > span:nth-child(1)"))).get_attribute('innerText').strip()
        if (param == "institution"):
            # h3.c-detail-header__subtitle
            return wait.until(EC.presence_of_element_located((
                By.CSS_SELECTOR, "h3.c-detail-header__subtitle"))).get_attribute('innerHTML').splitlines()[1].strip()
        if (param == "url"):
            return item_link
        if (param == "program_id"):
            # Generate ID from URL path segment (e.g., the number before the course name)
            return item_link.split('/')[-2]
            
        # --- List/Requirements Parameters (using original logic) ---
        if (param == 'admission_req'):
            return textcombiner("2","registration") # Index '2'
        if (param == 'language_req'):
            return textcombiner("4","registration") # Index '4'
        if (param == 'application_deadline'):
            return textcombiner("6","registration") # Index '6'
        if (param == 'submit_to'):
            return textcombiner("8","registration") # Index '8'
        if (param == 'semester_fee'):
            return textcombiner("4","costs") # Index '4'
        
        # --- NEW PARAMETERS - NEEDS HTML INSPECTION! ---
        if (param == "city"):
            # #<dd class="c-description-list__content mb-0">Kaiserslautern</dd>
            return extract_dt_dd_by_label("Course location")
            
        if (param == "tuition_fee"):
            # <dt class="c-description-list__content">Tuition fees per semester in EUR</dt>
            return extract_dt_dd_by_label("Tuition fees per semester in EUR")
            
        if (param == "start_date"):
            return extract_dt_dd_by_label("Beginning")
            
        if (param == "description"):
            return extract_dt_dd_by_label("Description/content")
            
        # Ensure all cases return something
        return "N/A"
            
    except Exception as e:
        # print(f"inside exception for parameter '{param}': ", e)
        logging.critical(e, exc_info=True)
        return "N/A" # Always return a default value on failure


def extractor(item_links):
    if (item_links):
        for item_link in item_links:
            try:
                print("## Visiting Link: ", item_link)
                driver.get(item_link)
                dataFromURL = []
                for param in params:
                    dataFromURL.append(paramData(param, item_link))
                
                # Check if all data is "N/A", if so, skip.
                if len(dataFromURL) < len(params) or all(item == 'N/A' for item in dataFromURL):
                    print("Skipping link due to failed extraction.")
                    continue

                #print("result: ", [f"{p}: {d}" for p, d in zip(params, dataFromURL)])

                final_data.append(dataFromURL)
                time.sleep(1)
                print("Done extracting from: ", item_link)
                time.sleep(3)
            except Exception as e:
                print(f'inside extractor loop exception for link {item_link}: {e}')
                logging.critical(e, exc_info=True)
                continue
    if not item_links:
        logging.critical("Empty item_links array.")


def exportJSON(): # <--- NEW FUNCTION
    filename = f"TESTING_MASTER_LIST_{PROGRAM_LIMIT}"

    if not final_data:
        print("No data to export.")
        return

    # Convert the list of lists (final_data) into a list of dictionaries
    json_data = []
    for row in final_data:
        # Zip the column names (cols) with the data row (row) to create a dictionary
        program_dict = dict(zip(cols, row))
        json_data.append(program_dict)

    # Save the data to a JSON file
    try:
        with open(f"./{filename}.json", 'w', encoding='utf-8') as f:
            # Use indent=4 for a pretty-printed JSON file
            json.dump(json_data, f, ensure_ascii=False, indent=4)
        print(f"\n✅ Data successfully exported to {filename}.json")
        # Print a sample of the JSON data
        print("\n--- JSON Sample ---")
        print(json.dumps(json_data[0], indent=4))
        print("-------------------\n")
    except Exception as e:
        print(f"Error saving JSON file: {e}")
        logging.critical("Error saving JSON file", exc_info=True)


def main():
    try:
        print("# Starting script ...")
        print(f"# Limit set to: {PROGRAM_LIMIT} programs.")
        print("# Visiting parent url: ", parent_url)
        item_links = surf1()
        
        # item_links is guaranteed to be a list (possibly empty) now
        
        print(f"Total links to extract: {len(item_links)}")
        extractor(item_links)
        exportJSON() # <--- CALL THE NEW JSON EXPORT FUNCTION
    except Exception as e:
        print(f"Error in main: {e}")
        logging.critical("Error in main function", exc_info=True)
    finally:
        print('inside finally')
        print("final_data length total: ", len(final_data))
        driver.quit()


if __name__ == "__main__":
    main()