import os
import random

from fastapi import FastAPI, HTTPException

from dotenv import load_dotenv

# environment variables
load_dotenv(override=True)

host = os.environ.get("host", "127.0.0.1")
logging_service_ports = list(map(int, os.environ.get("logging_service_ports", "50051").split(",")))
message_service_port = int(os.environ.get("messages_service_port", 8002))
            
# Facade Service
config_server = FastAPI()

@config_server.get("/")
def send_message(service_name: str):
    if service_name == "logging-service":
        urls = [f'{host}:{p}' for p in logging_service_ports]
        random.shuffle(urls)
        return urls
    elif service_name == "message-service":
        return [f'http://{host}:{message_service_port}/']

    raise HTTPException(status_code=404, detail="Service not found")    
