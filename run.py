import os
import multiprocessing

import uvicorn
from dotenv import load_dotenv

from facade_service.facade_service import facade_service
from logging_service.logging_service import serve
from messages_service.messages_service import message_service

load_dotenv(override=True)

host = os.environ.get("host", "127.0.0.1")
facade_service_port = int(os.environ.get("facade_service_port", 8000))
logging_service_port = int(os.environ.get("logging_service_port", 50051))
messages_service_port = int(os.environ.get("messages_service_port", 8002))


def run_facade():
    uvicorn.run(facade_service, host=host, port=facade_service_port)

def run_logging():
    serve(logging_service_port)
    
def run_messages():
    uvicorn.run(message_service, host=host, port=messages_service_port)

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
