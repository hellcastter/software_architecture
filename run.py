import os
import multiprocessing

import uvicorn
from dotenv import load_dotenv

from logging_service.logging_service import serve
from facade_service.facade_service import facade_service
from messages_service.messages_service import message_service
from config_server.config_server import config_server

load_dotenv(override=True)

host = os.environ.get("host", "127.0.0.1")
logging_service_ports = list(map(int, os.environ.get("logging_service_ports", "50051").split(",")))
facade_service_port = int(os.environ.get("facade_service_port", 8000))
config_server_port = int(os.environ.get("config_server_port", 8001))
messages_service_port = int(os.environ.get("messages_service_port", 8002))


def run_facade():
    uvicorn.run(facade_service, host=host, port=facade_service_port)

def run_logging(*ports):
    serve(*ports)
    
def run_messages():
    uvicorn.run(message_service, host=host, port=messages_service_port)
    
def run_config_server():
    uvicorn.run(config_server, host=host, port=config_server_port)

if __name__ == "__main__":   
    logging_services = []

    p1 = multiprocessing.Process(target=run_facade)
    p2 = multiprocessing.Process(target=run_messages)
    p3 = multiprocessing.Process(target=run_config_server)
    
    p1.start()
    p2.start()
    p3.start()
    
    for ports in zip(logging_service_ports, range(5701, 5701 + len(logging_service_ports))):
        p = multiprocessing.Process(target=run_logging, args=ports)
        p.start()
        logging_services.append(p)


    p1.join()
    p2.join()
    p3.join()

    for p in logging_services:
        p.join()
        
    os.system("pkill -f 'hazelcast'")
