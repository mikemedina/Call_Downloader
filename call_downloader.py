import datetime
import getpass
import os
import shutil
import time

from selenium import webdriver
from selenium.common.exceptions import NoSuchElementException
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.firefox.firefox_binary import FirefoxBinary


DOWNLOAD_DIR = 'C:/Users/mmedina/Downloads'
DEST_DIR = 'S:/Calls'
URL = 'https://commandcenter.securustech.net/SignonWeb/login/entrypage.jsp'
FIREFOX_PATH = 'C:/Users/mmedina/Desktop/Firefox/firefox.exe'

def main():
    """Download all available calls from the Securus Tech website.

    -Start Firefox
    -Log in to Securus Tech Call Monitoring
    -Execute the saved search query
    -Download all downloadable calls from the query
    -Move all downloaded calls from DOWNLOAD_DIR to DEST_DIR
    -Rename all downloaded calls to [hhmm] last, first.wav
    -Close Firefox
    """
    driver = setup_driver()
    driver.get(URL)
    login(driver)
    execute_search(driver)

    call_count = get_call_count(driver)
    for call_number in range(call_count):
        call_number_1indexed = call_number + 1
        inmate_name = get_inmate_name(driver, call_number)
        call_date, call_time = get_call_date_time(driver, call_number)
        print('Working on call {call_number_1indexed} of {call_count} by '
              '{inmate_name} on {call_date} at {call_time}'.format(**locals()))

        if already_listened_to(driver, call_number):
            print('Call #{} has already been listened to.\n'
                  .format(call_number_1indexed))
            continue

        try:
            dl_link = get_dl_link(driver, call_number)
        except NoSuchElementException:
            print("Call #{} is not available for download.\n"
                  .format(call_number_1indexed))
            continue

        print('Downloading #{}\n'.format(call_number_1indexed))
        download(dl_link)
        move_call(inmate_name, call_time)

    driver.quit()
    input('Done!')

def get_element(driver, xpath):
    """Return the element on the page at the given xpath."""
    elapsed_time = 0  # x100 milliseconds
    while True:
        try:
            return driver.find_element_by_xpath(xpath)
        except NoSuchElementException:
            if elapsed_time > 300:  # 30 seconds
                print('Timed out while looking for element')
                print('xpath: {}'.format(xpath))
            time.sleep(0.1)
            elapsed_time += 1

def setup_driver():
    """Set up Firefox."""
    # Points to Firefox
    binary = FirefoxBinary(FIREFOX_PATH)

    # This block should change the default download directory.
    # Unfortunately, it doesn't seem to do anything.
    profile = webdriver.FirefoxProfile()
    profile.set_preference('browser.download.folderList', 2)
    profile.set_preference('browser.download.manager.showWhenStarting', False)
    profile.set_preference('browser.download.dir', DOWNLOAD_DIR)
    profile.set_preference('browser.helperApps.neverAsk.saveToDisk',
                           'audio/wav')

    # Start browser
    return webdriver.Firefox(firefox_binary=binary, firefox_profile=profile)

def login(driver):
    """Prompt for username and password then log in."""
    user = input('Username: ')
    password = getpass.getpass()

    username_xpath = '//*[@id="j_username"]'
    username_field = get_element(driver, username_xpath)
    username_field.clear()
    username_field.send_keys(user)

    password_xpath = '//*[@id="j_password"]'
    password_field = get_element(driver, password_xpath)
    password_field.clear()
    password_field.send_keys(password)

    submit_button_xpath = ('/html/body/form[2]/'
                          'table[2]/tbody/tr/td/'
                          'table/tbody/tr/td[1]/'
                          'table/tbody/tr[6]/td/div/input')
    get_element(driver, submit_button_xpath).click()

def execute_search(driver):
    """Execute the designated search query."""
    saved_searches_xpath = ('//*[@id="callDetailLookupFormId"]/'
                            'table/tbody/tr[1]/td/a')
    get_element(driver, saved_searches_xpath).click()

    desired_query_xpath = ('//*[@id="contentDiv"]/'
                          'table/tbody/tr[2]/td/'
                          'table/tbody/tr[3]/td/'
                          'table/tbody/tr[2]/td/'
                          'table/tbody/tr[2]/td[1]/a[2]')
    get_element(driver, desired_query_xpath).click()

    # Between 00:00 and 07:00, change the start date to the previous day.
    now = datetime.datetime.now()
    if now.hour <= 7:
        search_start_xpath = '//*[@id="startDate"]'
        search_start = get_element(driver, search_start_xpath)
        search_start.clear()
        search_start.send_keys('{:02d}/{:02d}/{} 00:00:00'
            .format(now.month, now.day-1, now.year))

    execute_search_xpath = ('//*[@id="criteriaSectionId"]/'
                           'table/tbody/tr[3]/td/input[1]')
    get_element(driver, execute_search_xpath).click()

def get_call_count(driver):
    """Return the total number of calls."""
    call_count_xpath = ('//*[@id="callDetailLookupFormId"]/'
                       'table/tbody/tr[2]/td/'
                       'table/tbody/tr[4]/td/'
                       'table[1]/tbody/tr/td[1]')
    call_count_element = get_element(driver, call_count_xpath)

    return int(call_count_element.text.split()[0])

def get_inmate_name(driver, call_number):
    """Return the name of the inmate making the call."""
    inmate_name_xpath = ('//*[@id="callDetailLookupFormId"]/'
                        'table/tbody/tr[2]/td/'
                        'table/tbody/tr[4]/td/'
                        'table[2]/tbody/tr[1]/td/div/'
                        'table/tbody/tr[{}]/td[10]'.format(call_number+2))
    inmate_name_element = get_element(driver, inmate_name_xpath)
    return inmate_name_element.text.strip().title()

def get_call_date_time(driver, call_number):
    """Return the date a nd time of the inmate making the call."""
    call_time_xpath = ('//*[@id="callDetailLookupFormId"]/'
                      'table/tbody/tr[2]/td/'
                      'table/tbody/tr[4]/td/'
                      'table[2]/tbody/tr[1]/td/div/'
                      'table/tbody/tr[{}]/td[5]'.format(call_number+2))
    call_time_element = get_element(driver, call_time_xpath)
    return call_time_element.text.strip().split()

def already_listened_to(driver, call_number):
    """Return whether or not the call has been listened to."""
    call_log_xpath = ('/html/body/'
                     'table[1]/tbody/tr[3]/td/div[2]/form[5]/'
                     'table/tbody/tr[2]/td/'
                     'table/tbody/tr[4]/td/'
                     'table[2]/tbody/tr[1]/td/div/'
                     'table/tbody/tr[{}]/td[1]/'
                     'table/tbody/tr/td[2]/a[4]/img'.format(call_number+2))
    call_log = get_element(driver, call_log_xpath)

    # If a style exists, the call has NOT been listened to
    style = call_log.get_attribute('style')
    listened_to = not(bool(style))
    if not listened_to:
        # Page sometimes generates 'display: none;' without the space
        style = style.replace(' ', '')
        assert style == 'display:none;'
    return listened_to

def get_dl_link(driver, call_number):
    """Return the element representing the call's download link."""
    # get_element isn't used because it continues to look for the element
    # until timing out and sometimes this element won't exist
    dl_link_xpath = ('//*[@id="icon-row-{}"]/'
                    'table/tbody/tr/td[2]/a[5]'.format(call_number))
    return driver.find_element_by_xpath(dl_link_xpath)

def download(dl_link):
    """Download the specified call."""
    dl_link.click()

    # Wait for the download to begin
    while not any(name.endswith('.part') for name in os.listdir(DOWNLOAD_DIR)):
        time.sleep(0.1)

    # Wait for the download to complete
    while any(name.endswith('.part') for name in os.listdir(DOWNLOAD_DIR)):
        time.sleep(0.1)

def move_call(inmate_name, call_time):
    """Move the downloaded call from DOWNLOAD_DIR to DEST_DIR."""
    downloaded_call = next(name for name in os.listdir(DOWNLOAD_DIR)
                           if name.endswith('.wav'))

    # Change the time from hh:mm:ss to [hhmm]
    # because ':'s can't be used in file names
    first, last = inmate_name.split()
    call_time = ''.join(call_time.split(':')[:2])
    file_name = '[{call_time}] {last}, {first}.wav'.format(call_time=call_time,
                                                           last=last,
                                                           first=first)

    # Move the call to DEST_DIR using shutil in case DEST_DIR is off disk
    shutil.move(os.path.join(DOWNLOAD_DIR, downloaded_call),
              os.path.join(DEST_DIR, file_name))

if __name__ == '__main__':
    main()

