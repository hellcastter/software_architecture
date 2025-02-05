import os
import multiprocessing

import uvicorn
from dotenv import load_dotenv

from fastapi import FastAPI, HTTPException

from facade_service import facade_service
from logging_service import logging_service
from messages_service import message_service

env = load_dotenv()

host = os.environ.get("host", "127.0.0.1")
facade_service_host = os.environ.get("facade_service_host", 8000)
logging_service_host = os.environ.get("logging_service_host", 8001)
messages_service_host = os.environ.get("messages_service_host", 8002)

def run_facade():
    uvicorn.run(facade_service, host=host, port=facade_service_host)

def run_logging():
    uvicorn.run(logging_service, host=host, port=logging_service_host)
    
def run_messages():
    uvicorn.run(message_service, host=host, port=messages_service_host)

if __name__ == "__main__":   
    p1 = multiprocessing.Process(target=run_facade)
    p2 = multiprocessing.Process(target=run_logging)
    p3 = multiprocessing.Process(target=run_messages)
    
    p1.start()
    p2.start()
    p3.start()

    p1.join()
    p2.join()
    p3.join()
