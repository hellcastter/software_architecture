import grpc
from concurrent import futures

import logging_service.logging_pb2 as logging_pb2
import logging_service.logging_pb2_grpc as logging_pb2_grpc

class LoggingService(logging_pb2_grpc.LoggingService):
    def __init__(self):
        self.messages = {}

    def LogMessage(self, request, context):
        self.messages[request.uuid] = request.msg
        print(f"Logged message: {request.uuid} -> {request.msg}")
        return logging_pb2.LogResponse(status="success")
    
    def GetLogs(self, request, context):
        return logging_pb2.LogList(messages="\n".join(list(self.messages.values())))

def serve(port: int):
    server = grpc.server(futures.ThreadPoolExecutor(max_workers=10))
    logging_pb2_grpc.add_LoggingServiceServicer_to_server(LoggingService(), server)
    server.add_insecure_port(f'[::]:{port}')
    server.start()
    server.wait_for_termination()