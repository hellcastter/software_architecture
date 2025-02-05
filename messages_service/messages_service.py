from fastapi import FastAPI

message_service = FastAPI()

@message_service.get("/")
def send_message():
    return "Not implemented yet"