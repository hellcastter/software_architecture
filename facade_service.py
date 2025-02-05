import os
import uuid
import time

import requests
from dotenv import load_dotenv

from pydantic import BaseModel
from fastapi import FastAPI, HTTPException

# environment variables
env = load_dotenv()

host = os.environ.get("host", "127.0.0.1")
logging_service_port = os.environ.get("logging_service_port", 8001)
message_service_port = os.environ.get("message_service_port", 8002)

max_retries = int(os.environ.get("max_retries", 3))
retry_delay = int(os.environ.get("retry_delay", 2))
timeout = int(os.environ.get("timeout", 10))

# URLs
LOGGING_SERVICE_URL = f"http://{host}:{logging_service_port}/"
MESSAGE_SERVICE_URL = f"http://{host}:{message_service_port}/"

# Retry request
def retry_request(url: str, data: BaseModel):
    for attempt in range(1, max_retries + 1):
        try:
            response = requests.post(url, json=data, timeout=timeout)
            response.raise_for_status()
            return response
        except requests.exceptions.RequestException:
            if attempt < max_retries:
                print(f"Retrying №{attempt} failed: request to {url}")
                time.sleep(retry_delay)
            else:
                raise HTTPException(status_code=500, detail="Logging service error after retries")
            
# Facade Service
facade_service = FastAPI()

@facade_service.post("/")
def send_message(msg: str):
    unique_id = str(uuid.uuid4())
    data = {"uuid": unique_id, "msg": msg}
    
    retry_request(LOGGING_SERVICE_URL, data)
    
    return {"uuid": unique_id, "status": "logged"}


@facade_service.get("/")
def get_messages():
    try:
        response1 = requests.get(MESSAGE_SERVICE_URL)
        response1.raise_for_status()
    except requests.exceptions.RequestException as e:
        raise HTTPException(status_code=500, detail=f"Messages service error: {str(e)}")
    
    response2 = requests.get(LOGGING_SERVICE_URL)
    
    return {"message": response1.json(), "logs": response2.json()}
