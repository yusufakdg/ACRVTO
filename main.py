from fastapi import FastAPI, UploadFile, File, HTTPException
from google.cloud import storage
from google.oauth2 import service_account
import os
import json

app = FastAPI()

# Load credentials from environment variable
service_account_info = json.loads(os.getenv('GOOGLE_APPLICATION_CREDENTIALS'))
credentials = service_account.Credentials.from_service_account_info(service_account_info)
client = storage.Client(credentials=credentials)
bucket_name = os.getenv('GCS_BUCKET_NAME')
bucket = client.bucket(bucket_name)

@app.post("/upload/")
async def upload_file(file: UploadFile = File(...)):
    try:
        blob = bucket.blob(file.filename)
        blob.upload_from_file(file.file)
        return {"message": f"File '{file.filename}' uploaded successfully."}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

import os, json
cred = os.getenv('GOOGLE_APPLICATION_CREDENTIALS')
print("GOOGLE_APPLICATION_CREDENTIALS:", repr(cred))
service_account_info = json.loads(cred)

import json
with open("stately-century-300912-dc5bc153c25c.json", "r") as f:
    service_account_info = json.load(f)
os.environ['GOOGLE_APPLICATION_CREDENTIALS'] = json.dumps(service_account_info)