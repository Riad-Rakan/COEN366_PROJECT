# client.py
import socket
import random
from protocol import encode_msg, decode_msg, get_my_ip

SERVER_IP = '127.0.0.1'         # Replace with the actual IP of the computer running server.py
SERVER_TCP_PORT = 10000
SERVER_UDP_PORT = 20000

# Client's own details
CLIENT_NAME = "User1"
CLIENT_IP = get_my_ip
CLIENT_TCP_PORT = random.randint(50000, 55000)
CLIENT_UDP_PORT = random.randint(60000, 65000)

def register_with_server():
    client_tcp = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    
    try:
        print(f"[CLIENT] Connecting to Server at {SERVER_IP}:{SERVER_TCP_PORT}...")
        client_tcp.connect((SERVER_IP, SERVER_TCP_PORT))
        
        # Format: REGISTER | RQ# | Name | IP Address | TCP Socket# | UDP Socket#
        rq_num = random.randint(0, 200)
        msg_bytes = encode_msg("REGISTER", rq_num, CLIENT_NAME, CLIENT_IP, CLIENT_TCP_PORT, CLIENT_UDP_PORT)
        
        print("[CLIENT] Sending registration request...")
        client_tcp.send(msg_bytes)
        
        # Wait for the server's response
        response = client_tcp.recv(1024)
        parsed_response = decode_msg(response)
        print(f"[CLIENT] Server replied: {parsed_response}")
        
    except ConnectionRefusedError:
        print("[CLIENT] Connection failed. Is the server running?")
    finally:
        client_tcp.close()

if __name__ == "__main__":
    register_with_server()