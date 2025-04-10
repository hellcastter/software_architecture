import os
import uuid
import time
import grpc
import requests
from typing import Callable
from confluent_kafka import Producer

import requests
from dotenv import load_dotenv

from fastapi import FastAPI, HTTPException

import logging_service.logging_pb2 as logging_pb2
import logging_service.logging_pb2_grpc as logging_pb2_grpc

# environment variables
load_dotenv(override=True)

host = os.environ.get("host", "127.0.0.1")
config_server_port = int(os.environ.get("config_server_port", 8001))

max_retries = int(os.environ.get("max_retries", 3))
retry_delay = int(os.environ.get("retry_delay", 2))
timeout = int(os.environ.get("timeout", 10))

producer = Producer({'bootstrap.servers': 'localhost:9092,localhost:9093,localhost:9094'})

# Retry request
def retry_grpc_request(callback: Callable, data):
    response = requests.get(f"http://{host}:{config_server_port}/?service_name=logging-service")
    response.raise_for_status()
    logging_service_urls = response.json()
    
    print(logging_service_urls)
    
    for url in logging_service_urls:
        for attempt in range(1, max_retries + 1):
            try:
                return callback(data, url)
            except Exception as e:
                if attempt < max_retries:
                    print(f"Retrying №{attempt} at {url = } failed: request error: {str(e)}")
                    time.sleep(retry_delay)
        else:
            print(f"Retrying №{max_retries} at {url = } failed.")

    else:
        raise HTTPException(status_code=500, detail="Logging service error")

            
# Facade Service
facade_service = FastAPI()

def send_message_callback(data: logging_pb2.LogRequest, url: str):
    with grpc.insecure_channel(url) as channel:
        stub = logging_pb2_grpc.LoggingServiceStub(channel)
        response = stub.LogMessage(data, timeout=timeout)
  
    return response

@facade_service.post("/")
def send_message(msg: str):
    unique_id = str(uuid.uuid4())
    data = logging_pb2.LogRequest(uuid=unique_id, msg=msg)
    
    response = retry_grpc_request(send_message_callback, data)
    
    try:
        producer.produce('messages', key=unique_id, value=msg)
        producer.flush()
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    
    return {"uuid": unique_id, "status": response.status}


def get_messages_callback(data: logging_pb2.Empty, url: str):
    with grpc.insecure_channel(url) as channel:
        stub = logging_pb2_grpc.LoggingServiceStub(channel)
        response = stub.GetLogs(data, timeout=timeout)
            
    return response


@facade_service.get("/")
def get_messages():
    try:
        response = requests.get(f"http://{host}:{config_server_port}/?service_name=message-service")
        response.raise_for_status()
        MESSAGE_SERVICE_URL = response.json()[0]

        response1 = requests.get(MESSAGE_SERVICE_URL)
        response1.raise_for_status()
    except requests.exceptions.RequestException as e:
        raise HTTPException(status_code=500, detail=f"Messages service error: {str(e)}")

    response2 = retry_grpc_request(get_messages_callback, logging_pb2.Empty())

    return {"message": response1.json(), "logs": response2.messages}
