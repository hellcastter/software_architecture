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

from consul_service.consul_service import register_service, discover_service, deregister_service

PORT = 8000

# environment variables
load_dotenv(override=True)

max_retries = int(os.environ.get("max_retries", 3))
retry_delay = int(os.environ.get("retry_delay", 2))
timeout = int(os.environ.get("timeout", 10))

# Kafka producer setup
kafka_urls = discover_service("kafka", include_http=False)
bootstrap_servers = ",".join(kafka_urls)
print(f"Kafka bootstrap servers: {bootstrap_servers}")
producer = Producer({
    'bootstrap.servers': bootstrap_servers,
})

# Retry request
def retry_grpc_request(callback: Callable, data):
    logging_service_urls = discover_service("logging-service", include_http=False)
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
        message_service_url = discover_service("message-service")[0]

        print(f"Message service URL: {message_service_url}")
        response1 = requests.get(message_service_url)
        response1.raise_for_status()
    except requests.exceptions.RequestException as e:
        raise HTTPException(status_code=500, detail=f"Messages service error: {str(e)}")

    response2 = retry_grpc_request(get_messages_callback, logging_pb2.Empty())

    return {"message": response1.json(), "logs": response2.messages}

@facade_service.on_event("shutdown")
def shutdown_event():
    global PORT
    deregister_service(f"facade-service-id-{PORT}")
    print(f"Facade service with ID facade-service-id-{PORT} deregistered.")

if __name__ == "__main__":
    import uvicorn
    import argparse
    
    parser = argparse.ArgumentParser(description="Run the facade service.")
    parser.add_argument("--host", type=str, default="localhost", help="Host to run the service on.")
    parser.add_argument("--port", type=int, default=8100, help="Port to run the service on.")
    
    args = parser.parse_args()
    host = args.host
    PORT = int(args.port)
    
    print(f"Starting facade service on {host}:{PORT}")
    
    register_service("facade-service", f"facade-service-id-{PORT}", host, PORT)
    
    uvicorn.run(facade_service, host=host, port=PORT)