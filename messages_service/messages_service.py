from fastapi import FastAPI
from threading import Thread
from confluent_kafka import Consumer
import time
import os

message_service = FastAPI()

# In-memory store
messages = []

# Kafka consumer setup
conf = {
    'bootstrap.servers': 'localhost:9092,localhost:9093,localhost:9094',
    'group.id': f'message-group-{time.time()}',
    'auto.offset.reset': 'earliest'
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
    print("Messages:", messages)
    return messages