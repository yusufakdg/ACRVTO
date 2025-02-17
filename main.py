from fastapi import FastAPI, UploadFile, File, HTTPException
from google.cloud import storage
from google.oauth2 import service_account
import os
import json
import pandas as pd

app = FastAPI()

# Load credentials from environment variable
service_account_info = json.loads(os.getenv('GOOGLE_APPLICATION_CREDENTIALS'))
credentials = service_account.Credentials.from_service_account_info(service_account_info)
client = storage.Client(credentials=credentials)
bucket_name = os.getenv('GCS_BUCKET_NAME')
bucket = client.bucket(bucket_name)

# Load CSV data into a DataFrame
try:
    df = pd.read_csv(FİYAT_TEKLİFİ_ŞABLON.csv)
except FileNotFoundError:
    df = pd.DataFrame()  # Initialize an empty DataFrame if file not found

# Convert DataFrame to a list of dictionaries
items = df.to_dict(orient='records')

@app.get("/items/")
async def read_items():
    if not items:
        raise HTTPException(status_code=404, detail="No items found")
    return items

@app.get("/items/{item_id}")
async def read_item(item_id: int):
    for item in items:
        if item['id'] == item_id:  # Assuming 'id' is a column in your CSV
            return item
    raise HTTPException(status_code=404, detail="Item not found")

@app.post("/upload/")
async def upload_file(file: UploadFile = File(...)):
    try:
        blob = bucket.blob(file.filename)
        blob.upload_from_file(file.file)
        return {"message": f"File '{file.filename}' uploaded successfully."}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
