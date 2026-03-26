# server.py
import socket
import threading
from protocol import decode_msg, encode_msg
import json

TCP_PORT = 10000
UDP_PORT = 20000
HOST = '0.0.0.0' # Listens on all available network interfaces (important for multiple computers)

def handle_tcp_client(client_socket, address):
    """Handles an individual TCP connection (e.g., Registration)."""
    print(f"[TCP] Connection established with {address}")
    try:
        data = client_socket.recv(1024)
        if data:
            parsed_msg = decode_msg(data)
            print(f"[TCP] Received: {parsed_msg}")
            
            # TODO: Add your logic here (check if username exists, save to storage, etc.)
            if parsed_msg[0] == "REGISTER":
                rq_num = parsed_msg[1]
                # Send confirmation back
                response = encode_msg("REGISTERED", rq_num)
                client_socket.send(response)
                print(f"[TCP] Sent confirmation for RQ#{rq_num}")
                
    finally:
        client_socket.close()

def start_tcp_server():
    server_tcp = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server_tcp.bind((HOST, TCP_PORT))
    server_tcp.listen(5)
    print(f"[SERVER] TCP Listening on port {TCP_PORT}")
    
    while True:
        client_sock, addr = server_tcp.accept()
        # Start a new thread for each client that connects via TCP
        client_thread = threading.Thread(target=handle_tcp_client, args=(client_sock, addr))
        client_thread.start()

def start_udp_server():
    server_udp = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    server_udp.bind((HOST, UDP_PORT))
    print(f"[SERVER] UDP Listening on port {UDP_PORT}")
    
    while True:
        data, addr = server_udp.recvfrom(1024)
        parsed_msg = decode_msg(data)
        print(f"[UDP] Received from {addr}: {parsed_msg}")
        # TODO: Add logic to forward PUBLISH messages to interested users

if __name__ == "__main__":
    # Start both TCP and UDP servers simultaneously
    threading.Thread(target=start_tcp_server, daemon=True).start()
    threading.Thread(target=start_udp_server, daemon=True).start()
    
    # Keep the main thread alive
    input("[SERVER] Press Enter to shut down the server...\n")