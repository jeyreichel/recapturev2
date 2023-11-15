from app.solution import Solution
from app.settings import CAPTCHA_DEMO_URL


columns = {
            'first_name': "First Name",
            'last_name': "Last Name",
            'company': "-",
            'title': "-",
            'email': "-",
            'state': "-",
            'street': "Address",
            'city': "-",
            'zip_code': "-",
            'country': "-",
            'phone_number': "Mobile Phone 1",
            'message_template': "Hi {First Name} {Last Name},How are you doing?Are you owner of {Address}?Are you interested in my offer?",
        }

if __name__ == '__main__':
    Solution(url=CAPTCHA_DEMO_URL,file_path="csv/1.csv", columns=columns, begin_row=261, end_row=262).resolve()