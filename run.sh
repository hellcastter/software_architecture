#!/bin/bash

# Load environment variables from .env
set -a
source .env
set +a

# Set defaults
host=${host:-127.0.0.1}
logging_service_ports=${logging_service_ports:-50051}
message_service_ports=${message_service_ports:-8002}
facade_service_port=${facade_service_port:-8000}
config_server_port=${config_server_port:-8001}

# Flags
start_logging=false
start_messages=false
start_facade=false
start_config=false
stop_logging=false
stop_messages=false
stop_facade=false
stop_config=false

for arg in "$@"; do
  case $arg in
    --start-logging) start_logging=true ;;
    --start-messages) start_messages=true ;;
    --start-facade) start_facade=true ;;
    --start-config) start_config=true ;;
    --stop-logging) stop_logging=true ;;
    --stop-messages) stop_messages=true ;;
    --stop-facade) stop_facade=true ;;
    --stop-config) stop_config=true ;;
    --stop-all) stop_logging=true; stop_messages=true; stop_facade=true; stop_config=true ;;
    --start-all) start_logging=true; start_messages=true; start_facade=true; start_config=true ;;
    *) echo "Unknown argument: $arg"; exit 1 ;;
  esac
done

if $start_facade; then
  echo "Starting facade_service on port $facade_service_port..."
  uvicorn facade_service.facade_service:facade_service --host "$host" --port "$facade_service_port" &
fi

if $start_config; then
  echo "Starting config_server on port $config_server_port..."
  uvicorn config_server.config_server:config_server --host "$host" --port "$config_server_port" &
fi

if $start_logging; then
  IFS=',' read -ra logging_ports <<< "$logging_service_ports"
  i=0
  for port in "${logging_ports[@]}"; do
    hazelcast_port=$((5701 + i))
    echo "Starting logging_service on grpc port $port and hazelcast port $hazelcast_port..."
    python3 -c "from logging_service.logging_service import serve; serve($port, $hazelcast_port)" &
    ((i++))
  done
fi

if $start_messages; then
  IFS=',' read -ra message_ports <<< "$message_service_ports"
  for port in "${message_ports[@]}"; do
    echo "Starting message_service on port $port..."
    uvicorn messages_service.messages_service:message_service --host "$host" --port "$port" &
  done
fi

if $stop_facade; then
  echo "Stopping facade_service..."
  pkill -f "uvicorn.*facade_service"
fi

if $stop_config; then
  echo "Stopping config_server..."
  pkill -f "uvicorn.*config_server"
fi

if $stop_logging; then
  echo "Stopping logging services..."
  pkill -f "logging_service.logging_service"
  pkill -f "hazelcast"
fi

if $stop_messages; then
  echo "Stopping message services..."
  pkill -f "messages_service.messages_service"
fi

wait