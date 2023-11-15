from PIL import Image
import base64
from loguru import logger
from app.settings import CAPTCHA_RESIZED_IMAGE_FILE_PATH, CAPTCHA_TARGET_NAME_QUESTION_ID_MAPPING, MESSAGE_TEMPLATE, PHONE_NUMBER, MESSAGE_HISTORY_URL, FIRST_NAME, LAST_NAME, COMPANY_NAME, TITLE, EMAIL_ADDRESS, STREET_ADDRESS, CITY, STATE, ZIP_CODE, COUNTRY
import csv
import os
from datetime import datetime

PROGRESS_FILE = "csv/progress.txt"


def get_last_processed():
    if os.path.exists(PROGRESS_FILE):
        with open(PROGRESS_FILE, "r") as file:
            return int(file.read().strip())
    return 0


def save_last_processed(row_num):
    with open(PROGRESS_FILE, "w") as file:
        file.write(str(row_num))


def resize_base64_image(filename, size):
    width, height = size
    img = Image.open(filename)
    new_img = img.resize((width, height))
    new_img.save(CAPTCHA_RESIZED_IMAGE_FILE_PATH)
    with open(CAPTCHA_RESIZED_IMAGE_FILE_PATH, "rb") as f:
        data = f.read()
        encoded_string = base64.b64encode(data)
        return encoded_string.decode('utf-8')


def get_question_id_by_target_name(target_name):
    logger.debug(f'try to get question id by {target_name}')
    question_id = CAPTCHA_TARGET_NAME_QUESTION_ID_MAPPING.get(target_name)
    logger.debug(f'question_id {question_id}')
    return question_id


def convert_string_into_int(value):
    if len(value) == 0:
        return -1
    try:
        return int(value)
    except ValueError:
        return -1


def read_contacts_data(file_path, columns, begin_row, end_row):
    contact_list = []
    last_processed = get_last_processed()
    with open(file_path, 'r', encoding='utf-8-sig') as file:
        reader = csv.reader(file)

        for index, row in enumerate(reader):
            if (index == 0):
                logger.debug(f'{row}')
            else:
                break
    # logger.debug(f'begin row {type(begin_row)} {begin_row} end_row {type(end_row)} {end_row} last_processed {last_processed}')
    with open(file_path, 'r', encoding='utf-8-sig') as file:
        csv_readr = csv.DictReader(file)
        for index, row in enumerate(csv_readr, start=2):
            # Resume from where we left off
            if begin_row > 1 and index < begin_row: continue
            if end_row != -1 and index > end_row: break
            if index <= last_processed:
                continue
            contact_list.append({
                'message': replace_values_into_templage(row, columns),
                'phone_number': '1' + row.get(columns["phone_number"], "").strip(),
                'first_name': row.get(columns["first_name"], "").strip() if columns["first_name"] != "-" else "Unknown",
                'last_name': row.get(columns["last_name"], "").strip() if columns["last_name"] != "-" else "",
                'company': row.get(columns["company"], "").strip() if columns["company"] != "-" else "",
                'title': row.get(columns["title"], "").strip() if columns["title"] != "-" else "",
                'email': row.get(columns["email"], "").strip() if columns["email"] != "-" else "",
                'street': row.get(columns["street"], "").strip() if columns["street"] != "-" else "",
                'city': row.get(columns["city"], "").strip() if columns["city"] != "-" else "",
                'state': row.get(columns["state"], "").strip() if columns["state"] != "-" else "",
                'zip_code': row.get(columns["zip_code"], "").strip() if columns["zip_code"] != "-" else "",
                'country': row.get(columns["country"], "").strip() if columns["country"] != "-" else "",
            })

            # Save the progress
            save_last_processed(index)

        # If processing finishes, we can delete the progress file
        if os.path.exists(PROGRESS_FILE):
            os.remove(PROGRESS_FILE)
    
    return contact_list


def replace_values_into_templage(row, columns):
    message = columns['message_template']
    for value in columns.values():
        if len(value):
            message = message.replace("{" + value + "}", row.get(value, "").strip())
    return message


def write_message_history(phone_number, message):
    current_date = datetime.now().strftime("%Y-%m-%d")
    with open(f'{MESSAGE_HISTORY_URL}{current_date}.txt', 'a') as file:
        current_time = datetime.now().strftime("%H:%M:%S")
        file.write(f'{current_time} phone number: {phone_number}\n')
        file.write(f'\t message: {message}\n')


def contact_create_history(item):
    current_date = datetime.now().strftime("%Y-%m-%d")
    with open(f'{MESSAGE_HISTORY_URL}{current_date}.txt', 'a') as file:
        current_time = datetime.now().strftime("%H:%M:%S")
        file.write(f'{current_time} contact created\n')
        file.write(f'\t  Phone number: {item["phone_number"]} First name: {item["first_name"]} Last name: {item["last_name"]} Company: {item["company"]} Title: {item["title"]} Email Address: {item["email"]} Street Address: {item["street"]} City: {item["city"]} State: {item["state"]} Zip code: {item["zip_code"]} Country: {item["country"]} \n')


def contact_create_failed_history(item):
    current_date = datetime.now().strftime("%Y-%m-%d")
    with open(f'{MESSAGE_HISTORY_URL}{current_date}_failed.txt', 'a') as file:
        current_time = datetime.now().strftime("%H:%M:%S")
        file.write(f'{current_time} contact creation failed\n')
        file.write(f'\t  Phone number: {item["phone_number"]} First name: {item["first_name"]} Last name: {item["last_name"]} Company: {item["company"]} Title: {item["title"]} Email Address: {item["email"]} Street Address: {item["street"]} City: {item["city"]} State: {item["state"]} Zip code: {item["zip_code"]} Country: {item["country"]} \n')
