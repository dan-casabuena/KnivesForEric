import json
import os
import time
import unicodedata
import re
from typing import List
from urllib.parse import quote
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.wait import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import NoSuchElementException


############################################################
#                                                          #
#           Steam Community Market Item Scraper            #
#         By: Daniel Ray Casabuena (dan-casabuena)         #
#                  !!Use at own risk!!                     #
#                                                          #
############################################################

def userLogIn(driver: webdriver.Chrome, timeout: int) -> None:
    """
    Waits for the user to sign in to Steam through QR Code.
    Once timeout value is reached, the application will close.

    driver: A Chrome Web Driver
    timeout: integer value dictating max time spent waiting in seconds.
    """
    try:
        wait = WebDriverWait(driver, timeout).until(
            EC.title_is("Welcome to Steam")
        )
    except TimeoutError:
        driver.close()

def filterItems(driver: webdriver.Chrome, item: str) -> None:
    """
    Takes user requested item and searches it on steam market

    driver: A Chrome web driver
    item:   The search query to submit into Steam's search box.
            Must be specific as possible in order to prevent unwanted items
            to be searched. (str)
    """
    searchBar = driver.find_element(By.ID, "findItemsSearchBox").send_keys(item)
    searchBarSubmit = driver.find_element(By.ID, "findItemsSearchSubmit").click()


def grabItemsForSale(driver: webdriver.Chrome) -> List:
    """
    Grabs the names of all items in order to get hash values for requested items on the community market.

    As this does not use Steam API, this function may fail due to frequent and irregular timeouts.
    Timeouts may take up to an hour. Use at your own risk.

    driver: A Chrome Web Driver
    
    returns a list of item names (str) requested.
    """

    list_of_items = []

    try:
        next_button = driver.find_element(By.ID, "searchResults_btn_next")
        item_tray = driver.find_element(By.ID, "searchResultsRows")

        while next_button.get_attribute("class") == "pagebtn":
            for i in range(0, 10):
                element = driver.find_element(By.ID, "result_{}".format(i))
                list_of_items.append(element.get_attribute("data-hash-name"))
            driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
            next_button.click()
            
            while(item_tray.get_attribute("style") != "opacity: 1;"):
                time.sleep(4)

    except NoSuchElementException:
        pass
    
    return list_of_items

# Eventually: https://steamcommunity.com/market/pricehistory/?appid=730&market_hash_name=Glove%20Case%20Key
# ★ Bayonet | Damascus Steel (Minimal Wear)

def encodeItemURL(item: str) -> str:
    """
    Encodes item string into URL formatting and appends to the market price history URL.

    item: String parameter detailing the item name to be converted

    Returns a URL with the item appended to the steam market price history URL
    """
    toConcat = quote(item)
    return "https://steamcommunity.com/market/pricehistory/?appid=730&market_hash_name=" + toConcat


def slugify(value, allow_unicode=False):
    """
    Taken from https://github.com/django/django/blob/master/django/utils/text.py
    Convert to ASCII if 'allow_unicode' is False. Convert spaces or repeated
    dashes to single dashes. Remove characters that aren't alphanumerics,
    underscores, or hyphens. Convert to lowercase. Also strip leading and
    trailing whitespace, dashes, and underscores.
    """
    value = str(value)
    if allow_unicode:
        value = unicodedata.normalize('NFKC', value)
    else:
        value = unicodedata.normalize('NFKD', value).encode('ascii', 'ignore').decode('ascii')
    value = re.sub(r'[^\w\s-]', '', value.lower())
    return re.sub(r'[-\s]+', '-', value).strip('-_')

if __name__ == "__main__":
    mainApp = webdriver.Chrome()
    mainApp.get("https://store.steampowered.com/login/?redir=&redir_ssl=1&snr=1_4_4__global-header")

    userLogIn(mainApp, 100)

    # Get filtered list of knives and gloves NON STAT-TRAK, Min Wear.
    # TODO: Possibly add function to find any category you like, or have user choose filter first
    mainApp.get("https://steamcommunity.com/market/search?appid=730")

    itemsToConsider = input("Please input search query: ")
    filterItems(mainApp, itemsToConsider)
    time.sleep(1)

    item_list = grabItemsForSale(mainApp)

    try:
        os.mkdir("data")
    except FileExistsError:
        pass

    for item in item_list:
        itemURL = encodeItemURL(item)
        mainApp.get(itemURL)
        toExtract = mainApp.find_element_by_tag_name('pre').text
        parsed_json = json.loads(toExtract)

        if parsed_json['success'] != True:
            raise NoSuchElementException
        
        # Export json to manipulate later
        
        json_object = json.dumps(parsed_json, indent=4)

        with open("data/{}.json".format(slugify(item)), "w") as outfile:
            outfile.write(json_object)
        outfile.close()

        time.sleep(5)

    mainApp.close()