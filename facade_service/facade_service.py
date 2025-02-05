import os
import uuid
import time
import grpc
from typing import Callable

import requests
from dotenv import load_dotenv

from fastapi import FastAPI, HTTPException

import logging_service.logging_pb2 as logging_pb2
import logging_service.logging_pb2_grpc as logging_pb2_grpc

# environment variables
load_dotenv(override=True)

host = os.environ.get("host", "127.0.0.1")
logging_service_port = int(os.environ.get("logging_service_port", 50051))
message_service_port = int(os.environ.get("messages_service_port", 8002))

max_retries = int(os.environ.get("max_retries", 3))
retry_delay = int(os.environ.get("retry_delay", 2))
timeout = int(os.environ.get("timeout", 10))

# URLs
LOGGING_SERVICE_URL = f'{host}:{logging_service_port}'
MESSAGE_SERVICE_URL = f"http://{host}:{message_service_port}/"

# Retry request
def retry_grpc_request(callback: Callable, data):
    for attempt in range(1, max_retries + 1):
        try:
            return callback(data)
        except Exception as e:
            if attempt < max_retries:
                print(f"Retrying №{attempt} failed: request error: {str(e)}")
                time.sleep(retry_delay)
            else:
                raise HTTPException(status_code=500, detail="Logging service error after retries")
            
# Facade Service
facade_service = FastAPI()

def send_message_callback(data: logging_pb2.LogRequest):
    with grpc.insecure_channel(LOGGING_SERVICE_URL) as channel:
        stub = logging_pb2_grpc.LoggingServiceStub(channel)
        response = stub.LogMessage(data, timeout=timeout)
        
    return response

@facade_service.post("/")
def send_message(msg: str):
    unique_id = str(uuid.uuid4())
    data = logging_pb2.LogRequest(uuid=unique_id, msg=msg)
    
    response = retry_grpc_request(send_message_callback, data)
    
    return {"uuid": unique_id, "status": response.status}


def get_messages_callback(data: logging_pb2.Empty):
    with grpc.insecure_channel(LOGGING_SERVICE_URL) as channel:
        stub = logging_pb2_grpc.LoggingServiceStub(channel)
        response = stub.GetLogs(data, timeout=timeout)
        
    return response

@facade_service.get("/")
def get_messages():
    try:
        response1 = requests.get(MESSAGE_SERVICE_URL)
        response1.raise_for_status()
    except requests.exceptions.RequestException as e:
        raise HTTPException(status_code=500, detail=f"Messages service error: {str(e)}")

    response2 = retry_grpc_request(get_messages_callback, logging_pb2.Empty())

    return {"message": response1.json(), "logs": response2.messages}
