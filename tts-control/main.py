from fastapi import FastAPI, HTTPException, BackgroundTasks
from pydantic import BaseModel
import requests
import os

app = FastAPI()

# Configuration
TTS_API_URL = os.getenv("TTS_API_URL", "http://tts-api:8000/tts")
OUTPUT_FILE = "/app/output/owntone.wav"

class TTSRequest(BaseModel):
    text: str
    model_name: str = "ngocngan3701"
    speed: float = 1.0

@app.post("/synthesize")
async def synthesize(request: TTSRequest):
    try:
        # Prepare payload for TTS API
        payload = {
            "text": request.text,
            "model_name": request.model_name,
            "speed": request.speed
        }
        
        # Call TTS API
        # Note: tts-api returns the audio binary directly
        print(f"Forwarding request to {TTS_API_URL} with payload: {payload}")
        response = requests.post(TTS_API_URL, json=payload, headers={"Content-Type": "application/json", "Accept": "audio/wav"})
        
        response.raise_for_status()
        
        # Save to file
        print(f"Saving audio to {OUTPUT_FILE}")
        with open(OUTPUT_FILE, "wb") as f:
            f.write(response.content)
            
        return {"status": "success", "message": "Audio synthesized and saved as owntone.wav"}

    except requests.exceptions.RequestException as e:
        print(f"Error calling TTS API: {e}")
        raise HTTPException(status_code=500, detail=f"TTS API Error: {str(e)}")
    except Exception as e:
        print(f"General Error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/health")
def health():
    return {"status": "ok"}
