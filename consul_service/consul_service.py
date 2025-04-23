from consul import Consul

def register_service(service_name, service_id, address, port):
    consul = Consul()
    print(f"Registering service {service_name} with ID {service_id} at {address}:{port}.")
    consul.agent.service.register(
        name=service_name,
        service_id=service_id,
        address=address,
        port=int(port)
    )
    print(f"Service {service_name} registered with ID {service_id} at {address}:{port}.")
    

def discover_service(service_name, include_http=True):
    consul = Consul()
    _, nodes = consul.catalog.service(service_name)
    

    if include_http:
        print(f"Discovered {len(nodes)} nodes for service {service_name}.")
        return [f"http://{node['ServiceAddress']}:{node['ServicePort']}" for node in nodes]
    
    print(f"Discovered {len(nodes)} nodes for service {service_name} without HTTP.")
    return [f"{node['ServiceAddress']}:{node['ServicePort']}" for node in nodes]

def deregister_service(service_id):
    consul = Consul()
    consul.agent.service.deregister(service_id)
    print(f"Service with ID {service_id} deregistered.")