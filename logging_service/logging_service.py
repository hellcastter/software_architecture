import os
import grpc
import hazelcast
from concurrent import futures

import logging_service.logging_pb2 as logging_pb2
import logging_service.logging_pb2_grpc as logging_pb2_grpc

from consul_service.consul_service import register_service, deregister_service

PORT = 0

class LoggingService(logging_pb2_grpc.LoggingService):
    def __init__(self):
        self.client = hazelcast.HazelcastClient()
        self.messages = self.client.get_map("messages").blocking()

    def LogMessage(self, request, context):
        self.messages.put(request.uuid, request.msg)
        print(f"Logged message {PORT}: {request.uuid} -> {request.msg}")
        return logging_pb2.LogResponse(status="success")
    
    def GetLogs(self, request, context):
        return logging_pb2.LogList(messages="\n".join(list(self.messages.values())))
    
    def __del__(self):
        self.client.shutdown()
        deregister_service(f"logging-service-id-{PORT}")

def serve(port: int):
    global PORT
    PORT = port
    
    server = grpc.server(futures.ThreadPoolExecutor(max_workers=10))
    logging_pb2_grpc.add_LoggingServiceServicer_to_server(LoggingService(), server)
    server.add_insecure_port(f'[::]:{port}')
    server.start()
    
    register_service("logging-service", f"logging-service-id-{port}", "127.0.0.1", port)
    print(f"Logging service running at 127.0.0.1:{port}")
    
    server.wait_for_termination()