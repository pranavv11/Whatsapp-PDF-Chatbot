from fastapi import Request, Form, FastAPI
import os
import requests
from requests.auth import HTTPBasicAuth
from datetime import datetime, UTC
import pdfplumber
from dotenv import load_dotenv

load_dotenv()
TWILIO_ACCOUNT_SID=os.getenv("TWILIO_ACCOUNT_SID")
TWILIO_AUTH_TOKEN=os.getenv("TWILIO_AUTH_TOKEN")
TWILIO_PHONE_NUMBER=os.getenv("TWILIO_PHONE_NUMBER")

app = FastAPI()
media_dir = "Media"
os.makedirs(media_dir, exist_ok=True)



@app.post("/whatsapp-webhook")
async def whatsapp_webhook(
    request : Request,
    From: str = Form(...),
    Body: str = Form(""),
    NumMedia: int = Form(0),
    MediaContentType0: str = Form(None),
    MediaUrl0: str = Form(None),
):
    if int(NumMedia) > 0 and MediaUrl0:
        print(f"Received media: {MediaUrl0} of type {MediaContentType0}")
        extension = MediaContentType0.split("/")[-1]
        filename = f"{datetime.now(UTC).isoformat().replace(":", "_")}_{From.replace(":", "_")}.{extension}"
        file_path = os.path.join(media_dir, filename)

        media_res = requests.get(MediaUrl0, auth=HTTPBasicAuth(TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN))
        with open(file_path, 'wb') as f:
            f.write(media_res.content)

        extracted_text = ""
        if extension == "pdf":
            with pdfplumber.open(file_path) as pdf:
                for page in pdf.pages:
                    extracted_text += page.extract_text() or ""
        print(extracted_text)
    return {"status" : "Received"}