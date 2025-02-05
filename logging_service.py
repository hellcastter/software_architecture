from fastapi import FastAPI
from pydantic import BaseModel

logging_service = FastAPI()
message_store = {}

class Data(BaseModel):
    uuid: str
    msg: str

@logging_service.post("/")
def log_message(data: Data):
    message_store[data.uuid] = data.msg
    print(f"Logged message: {data.uuid} -> {data.msg}")
    return "success"


@logging_service.get("/")
def log_message():
    # get all messages without keys
    return "\n".join(list(message_store.values()))