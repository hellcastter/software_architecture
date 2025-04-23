from fastapi import FastAPI
from threading import Thread
from confluent_kafka import Consumer
import time
import os

from consul_service.consul_service import register_service, deregister_service, discover_service

message_service = FastAPI()

PORT = 8102

# In-memory store
messages = []

# Kafka consumer setup
kafka_urls = discover_service("kafka", include_http=False)
bootstrap_servers = ",".join(kafka_urls)
print(f"Kafka bootstrap servers: {bootstrap_servers}")
conf = {
    'bootstrap.servers': bootstrap_servers,
    'group.id': f'message-group-{time.time()}',
    'auto.offset.reset': 'earliest',
    "client.id": "messages-service"
}
consumer = Consumer(conf)
consumer.subscribe(['messages'])

def consume_messages():
    while True:
        msg = consumer.poll(1.0)
        
        if msg is None or msg.error():
            continue
        
        value = msg.value().decode('utf-8')
        print(f"Received message: {value}")

        messages.append( value )

# Start consumer in a background thread
Thread(target=consume_messages, daemon=True).start()
print(f"PID: {os.getpid()}")

@message_service.get("/")
def send_message():
    print("Fetching messages...")
    print("Messages:", messages)
    return messages
    
@message_service.on_event("shutdown")
def shutdown_event():
    global PORT
    deregister_service(f"message-service-id-{PORT}")
    print(f"Message service with ID message-service-id-{PORT} deregistered.")

if __name__ == "__main__":
    import uvicorn
    import argparse
    
    parser = argparse.ArgumentParser(description="Run the message service.")
    parser.add_argument("--host", type=str, default="localhost", help="Host to run the service on.")
    parser.add_argument("--port", type=int, default=8102, help="Port to run the service on.")
    
    args = parser.parse_args()
    host = args.host
    PORT = int(args.port)
    
    print(f"Starting message service on {host}:{PORT}")
    
    register_service("message-service", f"message-service-id-{PORT}", host, PORT)
    
    uvicorn.run(message_service, host=host, port=PORT)