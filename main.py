from fastapi import Request, Form, FastAPI
import os
import requests
from datetime import datetime
import pdfplumber

app = FastAPI()
media_dir = "Media"

@app.post("/whatsapp-webhook")
async def whatsapp_webhook(
    request : Request,
    From: str = Form(...),
    Body: str = Form(""),
    numMedia: int = Form(0),
    mediaType: str = Form(None),
    mediaURL: str = Form(None),
):
    if int(numMedia) > 0 and mediaURL:
        extension = mediaType.split("/")[-1]
        filename = f"{datetime.timestamp().isoformat()}_{From.replace(':', "_")}.{extension}"
        file_path = os.path.join(media_dir, filename)

        media_res = requests.get(mediaURL)
        with open(file_path, 'wb') as f:
            f.write(media_res.content)

        extracted_text = ""
        if extension == "pdf":
            with pdfplumber.open(file_path) as pdf:
                for page in pdf.pages:
                    extracted_text += page.extract_text() or ""
    
    return {"status" : "Received"}