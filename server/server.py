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

OTHER_SERVER_IP = '127.0.0.1'  # Replace with the actual IP address of Server 2

storage = json.load(open("storage.json", "r")) # Loads the storage.json file into a Python dictionary called 'storage'
users = json.load(open("users.json", "r")) # Loads the users.json file into a Python dictionary called 'users'

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
                handle_registration_request(client_socket, parsed_msg)
                
    finally:
        # TCP is a dedicated connection. Once the request is handled, we MUST close the pipeline.
        client_socket.close()

def handle_udp_client(data, address):
    """This function acts as a dedicated worker for a single UDP packet."""
    print(f"[UDP] Received from {address}: {data}")
    try:
        # Unpackages the raw bytes into a readable Python list (e.g., ['PUBLISH', '1', 'User1', ...])
        parsed_msg = decode_msg(data)
        print(f"[UDP] Parsed message: {parsed_msg}")
        
        # Checks if the first word in the message is the publish command
        if parsed_msg[0] == "PUBLISH":
            handle_publish_request(address, parsed_msg)
        elif parsed_msg[0] == "FORWARD":
            forward_publish_to_clients(parsed_msg[1], parsed_msg[2], parsed_msg[3], parsed_msg[4])
    finally:
        # UDP is connectionless, so we don't have a pipeline to close. We just finish this function and wait for the next packet.
        pass

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
        
        client_thread = threading.Thread(target=handle_udp_client, args=(data, addr))
        client_thread.start()

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


def handle_registration_request(client_socket, parsed_msg):
    # Grabs the Request Number (RQ#) from the list
    rq_num = parsed_msg[1]
    
    # Packages the success reply: REGISTERED | RQ#
    response = encode_msg("REGISTERED", rq_num)
    
    # Sends the packaged reply back down the active TCP pipeline to the client
    client_socket.send(response)
    print(f"[TCP] Sent confirmation for RQ#{rq_num}")


#========== 2.5. Users publishing and receiving messages on subjects of interest (over UDP) ==========
def handle_publish_request(address, parsed_msg):
    # Grabs the Request Number (RQ#) from the list
    rq_num = parsed_msg[1]

    name = parsed_msg[2]
    subject = parsed_msg[3]
    title = parsed_msg[4]
    text = parsed_msg[5]

    name_valid = False
    subject_valid = False

    for user in users:
        if name == user:
            name_valid = True
            break

    for subject in storage:
        if subject == subject:
            subject_valid = True
            break

    if not name_valid:
        response = encode_msg("PUBLISH-DENIED", rq_num, "Invalid Name")
        udp_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        udp_socket.sendto(response, address)
        print(f"[UDP] Sent PUBLISH-DENIED for RQ#{rq_num}: Invalid Name")
        return
    
    if not subject_valid:
        response = encode_msg("PUBLISH-DENIED", rq_num, "Invalid Subject")
        udp_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        udp_socket.sendto(response, address)
        print(f"[UDP] Sent PUBLISH-DENIED for RQ#{rq_num}: Invalid Subject")
        return
    
    #save article
    for subject in storage:
        if subject == subject:
            storage[subject].append({"title": title, "text": text})
            with open("storage.json", "w") as f:
                json.dump(storage, f, indent=4)
            break
    
    forward_publish_to_clients(name, subject, title, text)
    forward_publish_to_servers(name, subject, title, text)
    print(f"[UDP] Successfully handled PUBLISH request for RQ#{rq_num}. Forwarded to clients and servers.")
    
def forward_publish_to_clients(name, subject, title, text):
    # This function will be responsible for blasting the news out to all interested users over UDP.
    response = encode_msg("MESSAGE", name, subject, title, text)
    for user in users:
        if subject in users[user]["interests"]:
            user_ip = users[user]["ip"]
            user_udp_port = users[user]["udp_port"]
            udp_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            udp_socket.sendto(response, (user_ip, user_udp_port))
            print(f"[UDP] Forwarded message to {user} at {user_ip}:{user_udp_port}")

def forward_publish_to_servers(name, subject, title, text):
    # This function will be responsible for forwarding the news to other servers over UDP.
    response = encode_msg("FORWARD", name, subject, title, text)
    udp_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    if OTHER_SERVER_IP != '127.0.0.1': udp_socket.sendto(response, (OTHER_SERVER_IP, UDP_PORT)) #only send if there is a second server which is not localhost
    print(f"[UDP] Forwarded message to Server 2 at {OTHER_SERVER_IP}:{UDP_PORT}")


#========== 2.6 Commenting messages (over UDP) ==========
def handle_comment_request(parsed_msg):
    for subject in storage:
        if subject == parsed_msg[2]:
            for article in storage[subject]:
                if article["title"] == parsed_msg[3]:
                    for comment in article["comments"]:
                        if comment["name"] == parsed_msg[1] and comment["text"] == parsed_msg[4]:
                            print(f"[UDP] Duplicate comment detected. Ignoring.")
                            return
                    article["comments"].append({"name": parsed_msg[1], "text": parsed_msg[4]})
                    with open("storage.json", "w") as f:
                        json.dump(storage, f, indent=4)
                    break

    forward_publish_comment_to_servers(parsed_msg)
    forward_publish_comment_to_clients(parsed_msg[1], parsed_msg[2], parsed_msg[3], parsed_msg[4])

#PUBLISH-COMMENT is common between client->server and server->server, but client is the one who creates the encoded message.
def forward_publish_comment_to_servers(encoded_data):
    # This function will be responsible for forwarding the comment to other servers over UDP.
    udp_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    if OTHER_SERVER_IP != '127.0.0.1': udp_socket.sendto(encoded_data, (OTHER_SERVER_IP, UDP_PORT)) #only send if there is a second server which is not localhost
    print(f"[UDP] Forwarded comment to Server 2 at {OTHER_SERVER_IP}:{UDP_PORT}")

def forward_publish_comment_to_clients(name, subject, title, text):
    # This function will be responsible for blasting the comment out to all interested users over UDP.
    response = encode_msg("MESSAGE-COMMENT", name, subject, title, text)
    for user in users:
        if subject in users[user]["interests"]:
            user_ip = users[user]["ip"]
            user_udp_port = users[user]["udp_port"]
            udp_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            udp_socket.sendto(response, (user_ip, user_udp_port))
            print(f"[UDP] Forwarded comment to {user} at {user_ip}:{user_udp_port}")