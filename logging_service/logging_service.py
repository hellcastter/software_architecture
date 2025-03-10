import os
import grpc
import hazelcast
from concurrent import futures

import logging_service.logging_pb2 as logging_pb2
import logging_service.logging_pb2_grpc as logging_pb2_grpc

PORT = 0
HZ_PORT = 0

class LoggingService(logging_pb2_grpc.LoggingService):
    def __init__(self):
        # hz start -c "$PWD/hazelcast.xml" -p $port &
        os.system(f"hz start -c hazelcast.xml -p {HZ_PORT} &")

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

def serve(port: int, hz_port: int):
    global PORT, HZ_PORT
    PORT = port
    HZ_PORT = hz_port
    
    server = grpc.server(futures.ThreadPoolExecutor(max_workers=10))
    logging_pb2_grpc.add_LoggingServiceServicer_to_server(LoggingService(), server)
    server.add_insecure_port(f'[::]:{port}')
    server.start()
    server.wait_for_termination()