# server.py
import sys
sys.path.append("..")
# Imports the built-in library for handling network connections
import socket 
# Imports the threading library so the server can do multiple things at exactly the same time
import threading 
# Imports your custom helper functions to convert bytes to strings and back
from protocol import decode_msg, encode_msg 
# Imports the json library (useful later for saving your users to the storage.json file)
import json 

# --- SERVER CONFIGURATION ---
# The fixed port for all administrative "paperwork" (Registration, Updates, etc.)
TCP_PORT = 10000 
# The fixed port for blasting out and receiving the actual news broadcasts
UDP_PORT = 20000 
# '0.0.0.0' is a special address that tells the server to listen on ALL available network 
# interfaces (Wi-Fi, Ethernet, localhost). This is required if other computers are connecting to it.
HOST = '0.0.0.0' 

def handle_tcp_client(client_socket, address):
    """This function acts as a dedicated worker for a single TCP connection."""
    print(f"[TCP] Connection established with {address}")
    try:
        # Pauses this specific thread and waits to receive up to 1024 bytes of data from the client
        data = client_socket.recv(1024)
        
        # If the client sent data (and didn't just instantly disconnect)
        if data:
            # Unpackages the raw bytes into a readable Python list (e.g., ['REGISTER', '1', 'User1', ...])
            parsed_msg = decode_msg(data)
            print(f"[TCP] Received: {parsed_msg}")
            
            # Checks if the first word in the message is the registration command
            if parsed_msg[0] == "REGISTER":
                # Grabs the Request Number (RQ#) from the list
                rq_num = parsed_msg[1]
                
                # Packages the success reply: REGISTERED | RQ#
                response = encode_msg("REGISTERED", rq_num)
                
                # Sends the packaged reply back down the active TCP pipeline to the client
                client_socket.send(response)
                print(f"[TCP] Sent confirmation for RQ#{rq_num}")
                
    finally:
        # TCP is a dedicated connection. Once the request is handled, we MUST close the pipeline.
        client_socket.close()

def start_tcp_server():
    """This function sets up the TCP receptionist and loops forever."""
    # Creates a TCP socket (AF_INET = IPv4, SOCK_STREAM = TCP)
    server_tcp = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    
    # "Binds" (attaches) this socket to the computer's IP address and the designated TCP port
    server_tcp.bind((HOST, TCP_PORT))
    
    # Tells the socket to start listening for incoming connections. 
    # The '5' means it can hold up to 5 users in a waiting room if the server gets too busy.
    server_tcp.listen(5)
    print(f"[SERVER] TCP Listening on port {TCP_PORT}")
    
    # An infinite loop to keep the receptionist at the desk forever
    while True:
        # accept() blocks (freezes) this thread until a client actually connects.
        # When they do, it returns a new, dedicated socket just for them, and their IP address.
        client_sock, addr = server_tcp.accept()
        
        # Instead of handling the client right here (which would block other users from connecting),
        # we hire a new "worker" (a Thread) and hand them the client_sock to deal with in the background.
        client_thread = threading.Thread(target=handle_tcp_client, args=(client_sock, addr))
        
        # Starts the new background worker
        client_thread.start()

def start_udp_server():
    """This function sets up the UDP receptionist and loops forever."""
    # Creates a UDP socket (AF_INET = IPv4, SOCK_DGRAM = UDP)
    server_udp = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    
    # Binds the socket to the computer's IP and the designated UDP port
    server_udp.bind((HOST, UDP_PORT))
    print(f"[SERVER] UDP Listening on port {UDP_PORT}")
    
    # An infinite loop to catch flying packets
    while True:
        # recvfrom() freezes this thread until a UDP packet hits the port.
        # Because UDP is connectionless, it catches the raw 'data', and the 'addr' of whoever threw it.
        data, addr = server_udp.recvfrom(1024)
        
        # Decodes the raw bytes into a Python list
        parsed_msg = decode_msg(data)
        print(f"[UDP] Received from {addr}: {parsed_msg}")

# The guard block: only runs this startup sequence if you run server.py directly
if __name__ == "__main__":
    
    # We want both the TCP and UDP servers to run simultaneously without blocking each other.
    # So, we launch the TCP server loop in its own background thread.
    # daemon=True means this thread will automatically be killed if we close the main program.
    threading.Thread(target=start_tcp_server, daemon=True).start()
    
    # We launch the UDP server loop in a second background thread.
    threading.Thread(target=start_udp_server, daemon=True).start()
    
    # The two threads above are running in the background, so the main program needs a way to stay open.
    # This input() function simply pauses the main script until you press the Enter key in the terminal.
    input("[SERVER] Press Enter to shut down the server...\n")