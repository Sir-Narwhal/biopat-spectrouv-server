import socket

# Server details
SERVER_IP = '127.0.0.1'  # Localhost
SERVER_PORT = 12000

# Create a UDP socket
# client_socket = socket.socket(socket.SOCK_DGRAM)

with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as s: 
    s.bind(('', 0))
    print(f"socket name", s.getsockname())
    data, server_address = s.recvfrom()
    print(f"Received {len(data)} bytes from {server_address}: {data.decode('utf-8')}")



# # Receive a response from the server (optional)
# data, server_address = client_socket.recvfrom(1024)  # Buffer size 1024
# decoded_data = data.decode('utf-8')
# print(f"Received: '{decoded_data}' from {server_address[0]}:{server_address[1]}")

# # Close the socket
# client_socket.close()
