# VONAGE SMS SENDER

Sms sender in vonage platform using selenium

## Usage

Clone this repo:

```
https://github.com/cooldev900/recaptcha-v2-image-recognition.git
```

Then go to [https://yescaptcha.com/](https://yescaptcha.com/auth/register) and register your account, then get a `clientKey` from portal.

![image](https://github.com/cooldev900/recaptcha-v2-image-recognition/assets/13826499/de792d6d-b2ce-499d-9a3f-7e73af954c44)



Then create a `.env` file in root of this repo, and write this content:

```
CAPTCHA_RESOLVER_API_KEY=<Your Client Key>
CAPTCHA_DEMO_URL=<vonage login url>
USER_NAME=<username>
PASSWORD=<password>

COTACT_CSV_URL=<contact csv file path>
START_ROW_INDEX=<row number pointing the beginning of csv file, if not set, it will be 1 automatically due to header line>
END_ROW_INDEX=<row number pointing the endding of csv file, if not set, the last row number will be set automatically>

//We assume that row and column start from 0.
FIRST_NAME=<first name column name in csv>
LAST_NAME=<last name column name in csv>
COMPANY_NAME=<company column name in csv>
TITLE=<title column name in csv>
EMAIL_ADDRESS=<email address column name in csv>
STREET_ADDRESS=<street address column name in csv>
CITY=<city name column name in csv>
STATE=<state column name in csv>
ZIP_CODE=<zip code column name in csv>
COUNTRY=<country column name in csv>
PHONE_NUMBER=<phone number column name in csv>

MESSAGE_TEMPLATE="Hello ${FIRST_NAME} ${LAST_NAME},\n My name is Connor.\n I'm looking to acquire a few properties in the area.\n If you are the owner of ${STREET_ADDRESS}, would you consider an offer?"
```

Next, you need to install packages:

```
pip3 install -r requirements.txt
```

At last, run demo:

```
python3 main.py
```

Result:

![image](https://github.com/cooldev900/recaptcha-v2-image-recognition/assets/13826499/bde10300-362a-4e97-86b5-9f969b8a006c)


