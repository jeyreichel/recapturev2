from pickle import FALSE
from typing import List, Union
import requests
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.wait import WebDriverWait
from selenium.webdriver.remote.webelement import WebElement
import time
from loguru import logger
from app.captcha_resolver import CaptchaResolver
from app.settings import CAPTCHA_ENTIRE_IMAGE_FILE_PATH, CAPTCHA_SINGLE_IMAGE_FILE_PATH, USER_NAME, PASSWORD, COTACT_CSV_URL, MESSAGE_TEMPLATE, START_ROW_INDEX, END_ROW_INDEX
from app.utils import get_question_id_by_target_name, resize_base64_image, read_contacts_data, write_message_history, contact_create_history, contact_create_failed_history


class Solution(object):
    def __init__(self, url, file_path, columns, begin_row, end_row):
        self.file_path = file_path
        self.columns = columns
        self.begin_row = begin_row
        self.end_row = end_row
        options = webdriver.ChromeOptions()
        options.add_argument("--window-size=1920x1080")
        self.browser = webdriver.Chrome(options=options)
        self.browser.get(url)
        self.wait = WebDriverWait(self.browser, 200)
        self.captcha_resolver = CaptchaResolver()
        self.index = 0

    def __del__(self):
        time.sleep(10)
        self.browser.close()

    def get_all_frames(self) -> List[WebElement]:
        self.browser.switch_to.default_content()
        return self.browser.find_elements_by_tag_name('iframe')

    def get_captcha_entry_iframe(self) -> WebElement:
        self.browser.switch_to.default_content()
        captcha_entry_iframe = self.browser.find_element(By.CSS_SELECTOR,
                                                         'iframe[title="reCAPTCHA"]')
        return captcha_entry_iframe

    def switch_to_captcha_entry_iframe(self) -> None:
        captcha_entry_iframe: WebElement = self.get_captcha_entry_iframe()
        self.browser.switch_to.frame(captcha_entry_iframe)

    def get_captcha_content_iframe(self) -> WebElement:
        self.browser.switch_to.default_content()
        captcha_content_iframe = self.browser.find_element(By.CSS_SELECTOR,
                                                           'iframe[src*="bframe?"]')
        return captcha_content_iframe

    def switch_to_captcha_content_iframe(self) -> None:
        captcha_content_iframe: WebElement = self.get_captcha_content_iframe()
        self.browser.switch_to.frame(captcha_content_iframe)

    def get_entire_captcha_element(self) -> WebElement:
        entire_captcha_element: WebElement = self.wait.until(EC.element_to_be_clickable(
            (By.CSS_SELECTOR, '#rc-imageselect-target')))
        return entire_captcha_element

    def get_entire_captcha_natural_width(self) -> Union[int, None]:
        result = self.browser.execute_script(
            "return document.querySelector('div.rc-image-tile-wrapper > img').naturalWidth")
        if result:
            return int(result)
        return None

    def get_entire_captcha_display_width(self) -> Union[int, None]:
        entire_captcha_element = self.get_entire_captcha_element()
        if entire_captcha_element:
            return entire_captcha_element.rect.get('width')
        return None

    def trigger_captcha(self) -> None:
        self.switch_to_captcha_entry_iframe()
        captcha_entry = self.wait.until(EC.visibility_of_element_located(
            (By.ID, 'recaptcha-anchor')))
        captcha_entry.click()
        time.sleep(2)
        self.switch_to_captcha_content_iframe()
        entire_captcha_element: WebElement = self.get_entire_captcha_element()
        if entire_captcha_element.is_displayed:
            logger.debug('trigged captcha successfully')

    def get_captcha_target_name(self) -> WebElement:
        captcha_target_name_element: WebElement = self.wait.until(EC.visibility_of_element_located(
            (By.CSS_SELECTOR, '.rc-imageselect-desc-wrapper strong')))
        return captcha_target_name_element.text

    def get_verify_button(self) -> WebElement:
        verify_button = self.wait.until(EC.visibility_of_element_located(
            (By.CSS_SELECTOR, '#recaptcha-verify-button')))
        return verify_button

    def verify_single_captcha(self, index):
        has_object = True
        while has_object:
            time.sleep(10)
            elements = self.wait.until(EC.visibility_of_all_elements_located(
                (By.CSS_SELECTOR, '#rc-imageselect-target table td')))
            single_captcha_element: WebElement = elements[index]
            class_name = single_captcha_element.get_attribute('class')
            logger.debug(
                f'verifiying single captcha {index}, class {class_name}')
            if 'rc-imageselect-tileselected' in class_name:
                logger.debug(f'no new single captcha displayed')
                return
            logger.debug('new single captcha displayed')
            single_captcha_url = single_captcha_element.find_element(By.CSS_SELECTOR,
                                                                     'img').get_attribute('src')
            # logger.debug(f'single_captcha_url {single_captcha_url}')
            with open(CAPTCHA_SINGLE_IMAGE_FILE_PATH, 'wb') as f:
                f.write(requests.get(single_captcha_url).content)
            # with open("".join([CAPTCHA_SINGLE_IMAGE_FILE_PATH_SERIAL, "_", str(index), "_", str(self.index), ".png"]), 'wb') as f:
            #     self.index += 1
            #     f.write(requests.get(single_captcha_url).content)
            resized_single_captcha_base64_string = resize_base64_image(
                CAPTCHA_SINGLE_IMAGE_FILE_PATH, (100, 100))
            single_captcha_recognize_result = self.captcha_resolver.create_task(
                resized_single_captcha_base64_string, get_question_id_by_target_name(self.captcha_target_name))
            if not single_captcha_recognize_result:
                logger.error('count not get single captcha recognize result')
                return
            has_object = single_captcha_recognize_result.get(
                'solution', {}).get('hasObject')
            logger.debug(f'HadObject {self.index - 1} {has_object}')
            if has_object is None:
                logger.error('count not get captcha recognized indices')
                return
            if has_object is False:
                logger.debug('no more object in this single captcha')
                return
            if has_object:
                single_captcha_element.click()
                time.sleep(3)
            # check for new single captcha
            # self.verify_single_captcha(index)

    def get_verify_error_info(self):
        self.switch_to_captcha_content_iframe()
        self.browser.execute_script(
            "return document.querySelector('div.rc-imageselect-incorrect-response')?.text")

    def get_is_successful(self):
        self.switch_to_captcha_entry_iframe()
        anchor: WebElement = self.wait.until(EC.visibility_of_element_located((
            By.ID, 'recaptcha-anchor'
        )))
        checked = anchor.get_attribute('aria-checked')
        logger.debug(f'checked {checked}')
        return str(checked) == 'true'

    def get_is_failed(self):
        return bool(self.get_verify_error_info())

    def verify_entire_captcha(self):
        # check the if verify button is displayed
        verify_button: WebElement = self.get_verify_button()
        counter = 0
        while verify_button.is_displayed and verify_button.text != "VERIFY" and counter < 10:
            logger.debug(f'button text {verify_button.text}')
            verify_button.click()
            time.sleep(3)
            verify_button = self.get_verify_button()
            if counter == 10:
                logger.debug(f'Infinite captcha is more than 10.')
                return FALSE

        self.entire_captcha_natural_width = self.get_entire_captcha_natural_width()
        # logger.debug(
        #     f'entire_captcha_natural_width {self.entire_captcha_natural_width}'
        # )
        self.captcha_target_name = self.get_captcha_target_name()
        logger.debug(
            f'captcha_target_name {self.captcha_target_name}'
        )
        entire_captcha_element: WebElement = self.get_entire_captcha_element()
        entire_captcha_url = entire_captcha_element.find_element(By.CSS_SELECTOR,
                                                                 'td img').get_attribute('src')
        # logger.debug(f'entire_captcha_url {entire_captcha_url}')
        with open(CAPTCHA_ENTIRE_IMAGE_FILE_PATH, 'wb') as f:
            f.write(requests.get(entire_captcha_url).content)
        # logger.debug(
        #     f'saved entire captcha to {CAPTCHA_ENTIRE_IMAGE_FILE_PATH}')
        resized_entire_captcha_base64_string = resize_base64_image(
            CAPTCHA_ENTIRE_IMAGE_FILE_PATH, (self.entire_captcha_natural_width,
                                             self.entire_captcha_natural_width))
        # logger.debug(
        #     f'resized_entire_captcha_base64_string, {resized_entire_captcha_base64_string[0:100]}...')
        entire_captcha_recognize_result = self.captcha_resolver.create_task(
            resized_entire_captcha_base64_string,
            get_question_id_by_target_name(self.captcha_target_name)
        )
        if not entire_captcha_recognize_result:
            logger.error('count not get captcha recognize result')
            return
        recognized_indices = entire_captcha_recognize_result.get(
            'solution', {}).get('objects')
        if not recognized_indices:
            logger.error('count not get captcha recognized indices')
            return
        single_captcha_elements = self.wait.until(EC.visibility_of_all_elements_located(
            (By.CSS_SELECTOR, '#rc-imageselect-target table td')))
        logger.debug(f'captcha recogize indices {recognized_indices}')
        for recognized_index in recognized_indices:
            single_captcha_element: WebElement = single_captcha_elements[recognized_index]
            single_captcha_element.click()
            # check if need verify single captcha
            self.verify_single_captcha(recognized_index)

        # after all captcha clicked
        verify_button = self.get_verify_button()
        if verify_button.is_displayed:
            verify_button.click()
            logger.debug('verifed button clicked')
            time.sleep(3)

        is_succeed = self.get_is_successful()
        if is_succeed:
            logger.debug('verifed successfully')
        else:
            verify_error_info = self.get_verify_error_info()
            logger.debug(f'verify_error_info {verify_error_info}')
            # self.verify_entire_captcha()
        # return is_succeed

    def wait_body_loaded(self):
        self.browser.implicitly_wait(20)

    def enter_login_info(self):
        username = self.wait.until(EC.visibility_of_element_located(
            (By.ID, "userid")))
        username.send_keys(USER_NAME)
        password = self.wait.until(EC.visibility_of_element_located(
            (By.ID, "password")))
        password.send_keys(PASSWORD)
        remember_me = self.wait.until(EC.element_to_be_clickable(
            (By.CLASS_NAME, "Vlt-checkbox__button")))
        remember_me.click()

    def login(self):
        self.browser.switch_to.default_content()
        login_button: WebElement = self.wait.until(EC.element_to_be_clickable(
            (By.XPATH, '//vwc-button[@data-aid="login-button"]')))
        login_button.click()
        self.wait.until(EC.url_to_be("https://app.vonage.com/whats-new"))
        time.sleep(30)
        logger.debug(f'current url is {self.browser.current_url}')

    def go_to_sms_page(self):
        self.browser.switch_to.default_content()
        contact_dropdown = self.browser.find_element(
            By.CSS_SELECTOR, 'a[href="/my-apps/messages/sms"]')
        # logger.debug(f'new contact button {contact_dropdown.get_attribute("outerHTML")}')
        contact_dropdown.click()
        self.wait.until(EC.url_to_be(
            "https://app.vonage.com/my-apps/messages/sms"))
        logger.debug(f'current url is {self.browser.current_url}')

    def get_contacts_data(self):
        return read_contacts_data(self.file_path, self.columns, self.begin_row, self.end_row)

    def get_message_iframe(self) -> WebElement:
        self.browser.switch_to.default_content()
        captcha_entry_iframe = self.browser.find_element(By.CSS_SELECTOR,
                                                         'iframe[src="https://messaging.internal-apps.vonage.com"]')
        return captcha_entry_iframe

    def switch_to_message_iframe(self) -> None:
        captcha_entry_iframe: WebElement = self.get_message_iframe()
        self.browser.switch_to.frame(captcha_entry_iframe)

    def send_sms(self, phone_number, message):
        # click new button
        self.browser.switch_to.default_content()
        new_button = self.browser.find_element(By.CLASS_NAME, "new-button")
        new_button.click()
        time.sleep(1)
        # logger.debug(f'new sms button {new_button.get_attribute("outerHTML")}')

        new_dropdowns = self.browser.find_elements(
            By.CSS_SELECTOR, ".text-ellipsis.item-option-no-border.Vlt-dropdown__link")
        new_sms_button = new_dropdowns[1]
        new_sms_button.click()
        time.sleep(3)
        # logger.debug(f'buttons {new_dropdowns}')
        # logger.debug(f'new sms button {new_sms_button.get_attribute("outerHTML")}')

        # type phone number
        phone_input: WebElement = self.wait.until(EC.visibility_of_element_located(
            (By.CSS_SELECTOR, '#filterElement')))
        phone_input.send_keys(phone_number)
        time.sleep(1)
        # logger.debug(f'phone input {phone_input.get_attribute("outerHTML")}')

        # click append button
        phone_append_button: WebElement = self.wait.until(EC.element_to_be_clickable(
            (By.CLASS_NAME, 'button-append')))
        phone_append_button.click()
        time.sleep(1)
        # logger.debug(f'phone_append_button {phone_append_button.get_attribute("outerHTML")}')

        # type message
        self.switch_to_message_iframe()
        message_input: WebElement = self.wait.until(EC.visibility_of_element_located(
            (By.CLASS_NAME, 'ProseMirror')))
        message_input.send_keys(message)
        time.sleep(3)
        # logger.debug(f'phone input {message_input.get_attribute("outerHTML")}')

        # send message
        message_send_icon: WebElement = self.wait.until(EC.visibility_of_element_located(
            (By.CLASS_NAME, 'icon-template-purple')))
        message_send_icon.click()
        time.sleep(5)
        # logger.debug(f'phone input {message_send_icon.get_attribute("outerHTML")}')

    def convert_message(self, name, address):
        message = MESSAGE_TEMPLATE.replace('$name', name)
        message = message.replace('$address', address)
        return message

    def send_messages_to_contacts(self):
        contacts_data = self.get_contacts_data()
        total = 0
        for index, item in enumerate(contacts_data, start=1):
            self.send_sms(item['phone_number'], item['message'])
            write_message_history(item['phone_number'], item['message'])
            total += 1

        self.browser.quit()
        logger.debug(f'Total {total} of messages were sent successfully')

    def go_to_contact_page(self):
        self.browser.switch_to.default_content()
        contact_dropdown = self.wait.until(EC.element_to_be_clickable((
            By.CSS_SELECTOR, 'a[href="/contacts"]'
        )))
        # logger.debug(f'new contact button {contact_dropdown.get_attribute("outerHTML")}')
        contact_dropdown.click()
        self.wait.until(EC.url_to_be("https://app.vonage.com/contacts"))
        logger.debug(f'current url is {self.browser.current_url}')

    def create_contacts(self):
        contacts_data = self.get_contacts_data()
        total = 0
        for index, item in enumerate(contacts_data, start=1):
            successful = self.create_contact(item)
            if successful:
                total += 1
                contact_create_history(item)
                logger.debug(
                    f"The {index}th row of contact was created successfully")
            else:
                contact_create_failed_history(item)
                logger.debug(
                    f"The {index}th row of contact was created successfully")
        logger.debug(f'Total {total} of contacts were created successfully')

    def create_contact(self, item):
        # click new contact button
        # new_button_container = self.wait.until(EC.visibility_of_element_located((
        #     By.XPATH, '//div[@id="RouterView"]/div[1]/div[1]'
        # )))
        time.sleep(5)
        new_button = self.wait.until(EC.element_to_be_clickable((
            By.XPATH, '//button[@data-cy="title-button"]'
        )))
        new_button.click()

        self.wait.until(EC.visibility_of_element_located((
            By.XPATH, '//div[@data-cy="edit-contact-modal"]'
        )))

        first_name = self.wait.until(EC.visibility_of_element_located((
            By.XPATH, '//vwc-textfield[@data-cy="edit-contact-first-name"]'
        )))
        first_name = first_name.find_element(By.TAG_NAME, 'input')
        first_name.send_keys(item['first_name'])

        if len(item['last_name']) > 0:
            last_name = self.wait.until(EC.visibility_of_element_located((
                By.XPATH, '//vwc-textfield[@data-cy="edit-contact-last-name"]'
            )))
            last_name = last_name.find_element(By.TAG_NAME, 'input')

            last_name.send_keys(item['last_name'])

        if len(item['company']) > 0:
            company_name = self.wait.until(EC.visibility_of_element_located((
                By.XPATH, '//vwc-textfield[@data-cy="edit-contact-company-name"]'
            )))
            company_name = company_name.find_element(By.TAG_NAME, 'input')

            company_name.send_keys(item['company'])

        if len(item['title']) > 0:
            title = self.wait.until(EC.visibility_of_element_located((
                By.XPATH, '//vwc-textfield[@data-cy="edit-contact-title-name"]'
            )))

            title.send_keys(item['title'])

        phone_number_collpase = self.wait.until(EC.element_to_be_clickable((
            By.XPATH, '//div[@data-cy="phone-number-block"]/div[1]'
        )))
        phone_number_collpase.click()

        phone_number_block0 = self.wait.until(EC.visibility_of_element_located((
            By.XPATH, '//div[@data-cy="edit-contact-phone-number-0"]'
        )))
        phone_number_input = phone_number_block0.find_element(
            By.TAG_NAME, 'input')
        phone_number_input.send_keys(item['phone_number'])

        if len(item['email']) > 0:
            email_address_collpase = self.wait.until(EC.element_to_be_clickable((
                By.XPATH, '//div[@data-cy="email-block"]/div[1]'
            )))
            email_address_collpase.click()

            email_address_block0 = self.wait.until(EC.visibility_of_element_located((
                By.XPATH, '//div[@data-cy="email-block"]/div[2]'
            )))
            email_address_input = email_address_block0.find_element(
                By.TAG_NAME, 'input')
            email_address_input.send_keys(item['email'])

        # street_address_block = self.wait.until(EC.visibility_of_element_located((
        #     By.XPATH, '//div[@data-cy="address-block"]'
        # )))
        street_address_collpase = self.wait.until(EC.element_to_be_clickable((
            By.XPATH, '//div[@data-cy="address-block"]/div[1]'
        )))
        street_address_collpase.click()

        street_address_block0 = self.wait.until(EC.visibility_of_element_located((
            By.XPATH, '//div[@data-cy="address-block"]/div[2]/div[1]/div[2]/div[2]'
        )))

        if len(item['street']) > 0:
            city_input = street_address_block0.find_element(
                By.XPATH, '//div[@data-cy="edit-contact-address"]/div[1]/div[1]/input[1]')
            city_input.send_keys(item['street'])
        if len(item['city']) > 0:
            city_input = street_address_block0.find_element(
                By.XPATH, '//div[@data-cy="edit-contact-city"]/div[1]/div[1]/input[1]')
            city_input.send_keys(item['city'])

        if len(item['state']) > 0:
            state_input = street_address_block0.find_element(
                By.XPATH, '//div[@data-cy="edit-contact-state"]/div[1]/div[1]/input[1]')
            state_input.send_keys(item['state'])

        if len(item['zip_code']) > 0:
            zip_input = street_address_block0.find_element(
                By.XPATH, '//div[@data-cy="edit-contact-zipCode"]/div[1]/div[1]/input[1]')
            zip_input.send_keys(item['zip_code'])

        if len(item['country']):
            country_input = street_address_block0.find_element(
                By.XPATH, '//div[@data-cy="edit-contact-country"]/div[1]/div[1]/input[1]')
            country_input.send_keys(item['country'])

        create_button = self.wait.until(EC.element_to_be_clickable((
            By.XPATH, '//div[@class="save-cancel"]/button[2]'
        )))
        if "Vlt-btn--disabled" in create_button.get_attribute('class'):
            close_button = self.wait.until(EC.element_to_be_clickable((
                By.XPATH, '//div[@class="save-cancel"]/button[1]'
            )))
            close_button.click()
            return False
        else:
            create_button.click()
            time.sleep(5)
            return True

    def resolve(self):
        self.wait_body_loaded()
        self.enter_login_info()
        self.trigger_captcha()
        self.verify_entire_captcha()
        self.login()
        self.go_to_contact_page()
        self.create_contacts()
        self.go_to_sms_page()
        self.send_messages_to_contacts()
