from typing import Union

from fastapi import FastAPI, Form, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from app.solution import Solution
from app.settings import CAPTCHA_DEMO_URL

app = FastAPI()

origins = [
    "*",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_methods=["*"],
    allow_headers=["*"],
    allow_credentials=True,
)

@app.get("/")
def read_root():
    return {"Hello": "World"}

class Item(BaseModel):    
    csvfile: bytes
    firstName: str
    lastName: str
    company: str
    title: str
    email: str
    street: str
    city: str
    state: str
    zipcode: str
    country: str
    phoneNumber: str
    messageTemplate: str

@app.post("/send_sms")
async def send_sms(csvfile: UploadFile  = File(...), firstName: str = Form(...), lastName: str = Form(), company: str = Form(), title: str = Form(), email: str = Form(), street: str = Form(...), city: str = Form(), state: str = Form(), zipcode: str = Form(), country: str = Form(), phoneNumber: str = Form(...), messageTemplate: str = Form(...), beginRow: int = Form(), endRow: int = Form() ):
    # Do something with the data
    file_content = await csvfile.read()  # Read the uploaded file content
    file_path = f"csv/{csvfile.filename}"

    with open(file_path, "wb") as f:
        f.write(file_content)
    
    columns = {
        'first_name': firstName,
        'last_name': lastName,
        'company': company,
        'title': title,
        'email': email,
        'street': street,
        'city': city,
        'zip_code': zipcode,
        'country': country,
        'phone_number': phoneNumber,
        'message_template': messageTemplate,
        'state': state
    }

    try:
        solution = Solution(url=CAPTCHA_DEMO_URL, file_path=file_path, columns=columns, end_row=endRow, begin_row=beginRow)
        await solution.resolve()
        return {"result": "success"}
    except Exception as e:
        return {"result": "failed", "message": str(e)}
        

    