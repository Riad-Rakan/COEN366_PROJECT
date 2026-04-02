# client.py

import socket                                           # Imports Python's built-in library for handling network connections (both TCP and UDP)
import random                                           # Imports the random library to generate random request numbers and ports
import sys
sys.path.append("..")
from protocol import encode_msg, decode_msg, get_my_ip  # Imports your custom helper functions from your shared protocol.py file


# --- SERVER CONFIGURATION ---
SERVER_IP = '127.0.0.1'                                 # The IP address of the machine running server.py (Change this when testing on multiple computers)
SERVER_TCP_PORT = 10000                                 # The fixed TCP port the server is listening on for administrative tasks (like Registration)
SERVER_UDP_PORT = 20000                                 # The fixed UDP port the server uses to blast out news messages

# --- CLIENT CONFIGURATION ---
CLIENT_NAME = "User1"                                   # The unique name for this specific user in the News Sharing System
CLIENT_IP = get_my_ip()                                 # Calls your helper function to automatically find this computer's local IP address
CLIENT_TCP_PORT = random.randint(50000, 55000)          # Randomly selects a TCP port for the client to use (prevents conflicts if testing multiple clients on one PC)
CLIENT_UDP_PORT = random.randint(60000, 65000)          # Randomly selects a UDP port for the client to listen for incoming news on

def register_with_server():
    # Creates a new socket object. 
    # AF_INET means we are using standard IPv4 addresses. 
    # SOCK_STREAM means we are using TCP (a reliable, connection-oriented protocol).
    client_tcp = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    
    try:
        print(f"[CLIENT] Connecting to Server at {SERVER_IP}:{SERVER_TCP_PORT}...")
        client_tcp.connect((SERVER_IP, SERVER_TCP_PORT))# Attempts to establish the actual TCP connection handshake with the server
        rq_num = random.randint(0, 200)                 # Generates a random Request Number (RQ#) to track this specific registration attempt

        
        # Uses your helper function to package the variables into a pipe-separated byte string.
        # Format according to PDF: REGISTER | RQ# | Name | IP Address | TCP Socket# | UDP Socket#
        msg_bytes = encode_msg("REGISTER", rq_num, CLIENT_NAME, CLIENT_IP, CLIENT_TCP_PORT, CLIENT_UDP_PORT)
        
        print("[CLIENT] Sending registration request...")
        # Sends the packaged byte string over the active TCP connection to the server
        client_tcp.send(msg_bytes)
        
        # Pauses the script and waits to receive up to 1024 bytes of data back from the server
        response = client_tcp.recv(1024)
        
        # Unpackages the raw bytes from the server back into a readable Python list
        parsed_response = decode_msg(response)
        
        # Prints the server's reply (which should be something like ['REGISTERED', '150'])
        print(f"[CLIENT] Server replied: {parsed_response}")
        
    except ConnectionRefusedError:
        # If the server isn't running or the IP/Port is wrong, this catches the error so the program doesn't crash
        print("[CLIENT] Connection failed. Is the server running?")
    finally:
        # Regardless of success or failure, TCP requires you to close the connection when finished
        client_tcp.close()

# The guard block: only runs the registration function if you execute this file directly from the terminal
if __name__ == "__main__":
    register_with_server()

#2.5. Users publishing and receiving messages on subjects of interest (over UDP)
def request_publish(name, subject, title, text):
    client_udp = socket.socket(socket.AF_INET, socket.SOCK_DGRAM) # Creates a new socket object for UDP communication
    rq_num = random.randint(0, 200) # Generates a random Request Number (RQ#) to track this specific publish attempt

    # Uses your helper function to package the variables into a pipe-separated byte string.
    # Format: PUBLISH | RQ# | Name | Subject | Title | Text
    msg_bytes = encode_msg("PUBLISH", rq_num, name, subject, title, text)
    print(f"[CLIENT] Sending PUBLISH request for RQ#{rq_num}...")
    # Sends the packaged byte string over UDP to the server's IP and UDP port
    client_udp.sendto(msg_bytes, (SERVER_IP, SERVER_UDP_PORT))

#2.6 Commenting messages (over UDP)
#Publish Comment is created by a client and sent to server. This will be forwarded to the other server as-is
def publish_comment(name, subject, title, text):
    client_udp = socket.socket(socket.AF_INET, socket.SOCK_DGRAM) # Creates a new socket object for UDP communication
    rq_num = random.randint(0, 200) # Generates a random Request Number (RQ#) to track this specific comment attempt

    # Uses your helper function to package the variables into a pipe-separated byte string.
    # Format: PUBLISH-COMMENT | RQ# | Name | Subject | Title | Text
    msg_bytes = encode_msg("PUBLISH-COMMENT", rq_num, name, subject, title, text)
    print(f"[CLIENT] Sending PUBLISH-COMMENT request for RQ#{rq_num}...")
    # Sends the packaged byte string over UDP to the server's IP and UDP port
    client_udp.sendto(msg_bytes, (SERVER_IP, SERVER_UDP_PORT))
