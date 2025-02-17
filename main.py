from fastapi import FastAPI, UploadFile, File, HTTPException
from google.cloud import storage
from google.oauth2 import service_account
import openai
import os
import json
import pandas as pd
from typing import List
from pydantic import BaseModel
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from fastapi.middleware.cors import CORSMiddleware 
import tempfile
from pathlib import Path

app = FastAPI(title="Price Offer Generator API")

# Load environment variables
openai.api_key = os.getenv('OPENAI_API_KEY')
service_account_info = json.loads(os.getenv('GOOGLE_APPLICATION_CREDENTIALS'))
credentials = service_account.Credentials.from_service_account_info(service_account_info)
client = storage.Client(credentials=credentials)
bucket_name = os.getenv('GCS_BUCKET_NAME')
bucket = client.bucket(bucket_name)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount the static directory
app.mount("/static", StaticFiles(directory="static"), name="static")

@app.get("/")
async def read_root():
    return FileResponse('static/index.html')


class PriceOffer(BaseModel):
    customer_name: str
    project_description: str
    estimated_price: float
    details: dict

@app.post("/transcribe-and-generate-offer/")
async def transcribe_and_generate_offer(audio_file: UploadFile = File(...)):
    try:
        # Save the uploaded audio file temporarily
        with tempfile.NamedTemporaryFile(delete=False, suffix=Path(audio_file.filename).suffix) as temp_audio:
            content = await audio_file.read()
            temp_audio.write(content)
            temp_audio.flush()

        # Transcribe audio using Whisper AI
        with open(temp_audio.name, "rb") as audio_file:
            transcript = openai.Audio.transcribe("whisper-1", audio_file)

        # Generate price offer using GPT
        prompt = f"""
        Based on the following conversation transcript, generate a detailed price offer.
        Include project requirements, scope, and estimated costs.
        
        Conversation:
        {transcript['text']}
        
        Generate a structured price offer in JSON format with customer name, 
        project description, estimated price, and detailed breakdown.
        """

        completion = openai.ChatCompletion.create(
            model="gpt-4",
            messages=[
                {"role": "system", "content": "You are a professional business analyst who creates detailed price offers."},
                {"role": "user", "content": prompt}
            ]
        )

        # Parse the AI-generated offer
        offer_data = json.loads(completion.choices[0].message.content)
        price_offer = PriceOffer(**offer_data)

        # Store the offer in GCS
        offer_filename = f"offers/{price_offer.customer_name}_{pd.Timestamp.now().strftime('%Y%m%d_%H%M%S')}.json"
        blob = bucket.blob(offer_filename)
        blob.upload_from_string(json.dumps(offer_data))

        # Clean up temporary file
        os.unlink(temp_audio.name)

        return {
            "message": "Price offer generated successfully",
            "offer": price_offer,
            "stored_file": offer_filename
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/offers/", response_model=List[PriceOffer])
async def list_offers():
    try:
        offers = []
        blobs = bucket.list_blobs(prefix="offers/")
        for blob in blobs:
            offer_data = json.loads(blob.download_as_string())
            offers.append(PriceOffer(**offer_data))
        return offers
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/offer/{customer_name}")
async def get_customer_offers(customer_name: str):
    try:
        offers = []
        blobs = bucket.list_blobs(prefix=f"offers/{customer_name}")
        for blob in blobs:
            offer_data = json.loads(blob.download_as_string())
            offers.append(offer_data)
        if not offers:
            raise HTTPException(status_code=404, detail="No offers found for this customer")
        return offers
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

