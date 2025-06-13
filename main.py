from fastapi import Request, Form, FastAPI
import os
import requests
from requests.auth import HTTPBasicAuth
from datetime import datetime, UTC
import pdfplumber
from dotenv import load_dotenv
from transformers import pipeline
from typing import List

load_dotenv()
TWILIO_ACCOUNT_SID=os.getenv("TWILIO_ACCOUNT_SID")
TWILIO_AUTH_TOKEN=os.getenv("TWILIO_AUTH_TOKEN")
TWILIO_PHONE_NUMBER=os.getenv("TWILIO_PHONE_NUMBER")

app = FastAPI()
media_dir = "Media"
os.makedirs(media_dir, exist_ok=True)

user_context = {}
ques_ans = pipeline("question-answering", model="deepset/roberta-base-squad2")

def chunk_text(text:str, chunk_size:int = 500, overlap:int = 100) -> List[str]:
    words = text.split()
    chunks = []
    for i in range(0, len(words), chunk_size-overlap):
        chunk = words[i:i+chunk_size]
        chunks.append(" ".join(chunk))
    return chunks

def answer_question(context_chunk:List[str], question:str) -> str:
    best_answer = ""
    best_score = 0

    for chunk in context_chunk: 
        try:
            result = ques_ans({
                "context" : chunk,
                "question" : question
            })
            if result['score'] > best_score:
                best_score = result['score']
                best_answer = result['answer']
        except Exception as e:
            continue
    return best_answer or "Sorry, couldn't find an answer"

def send_reply(to: str, message: str):
    url = f"https://api.twilio.com/2010-04-01/Accounts/{TWILIO_ACCOUNT_SID}/Messages.json"
    data = {
        "From": TWILIO_PHONE_NUMBER,
        "To": to,
        "Body": message
    }
    response = requests.post(url, data=data, auth=HTTPBasicAuth(TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN))
    print("Reply status: ", response.status_code)



@app.post("/whatsapp-webhook")
async def whatsapp_webhook(
    request : Request,
    From: str = Form(...),
    Body: str = Form(""),
    NumMedia: int = Form(0),
    MediaContentType0: str = Form(None),
    MediaUrl0: str = Form(None),
):
    user_id = From.strip()
    if int(NumMedia) > 0 and MediaUrl0:
        try:
            if user_id:
                print("User id is: ", user_id)
        except Exception as e: 
            print("Userid doesn't exist")
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
        # print(extracted_text)

        user_context[user_id] = chunk_text(extracted_text)
        send_reply(user_id, "Document received!! Ask questions")

        return {"status" : "Document_Received"}

    elif Body and user_id in user_context:
        chunks = user_context[user_id]
        answer = answer_question(chunks, Body)
        send_reply(user_id, answer)

        return{"status": "Answered"}
    
    else:
        send_reply(user_id, "Send a document first")
        return{"status": "Awaiting_document"}