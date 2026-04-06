# client.py

import socket                                           # Imports Python's built-in library for handling network connections (both TCP and UDP)
import random                                           # Imports the random library to generate random request numbers and ports
import sys
import threading                                        # Imports threading library for concurrent listening operations
sys.path.append("..")
import tcp_handler, udp_handler
from protocol import encode_msg, decode_msg, get_my_ip  # Imports your custom helper functions from your shared protocol.py file

class Client:

    # --- SERVER CONFIGURATION ---
    SERVER_IP = '100.100.238.78'                                 # The IP address of the machine running server.py (Change this when testing on multiple computers)
    SERVER_TCP_PORT = 10000                                 # The fixed TCP port the server is listening on for administrative tasks (like Registration)
    SERVER_UDP_PORT = 20000                                 # The fixed UDP port the server uses to blast out news messages

    # --- CLIENT CONFIGURATION ---
    name = ""                                   # The unique name for this specific user in the News Sharing System
    #CLIENT_IP = '100.78.41.47'                                # Uncomment to manually assign IP address
    CLIENT_IP = get_my_ip()                                 # Calls your helper function to automatically find this computer's local IP address
    CLIENT_TCP_PORT = random.randint(50000, 55000)          # Randomly selects a TCP port for the client to use (prevents conflicts if testing multiple clients on one PC)
    CLIENT_UDP_PORT = random.randint(60000, 65000)          # Randomly selects a UDP port for the client to listen for incoming news on

    def __init__(self):
        self.name = ""
        self.udp_sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM) # Create a UDP socket for sending messages
        self.udp_sock.bind((self.CLIENT_IP, self.CLIENT_UDP_PORT))  # Bind to the client's listening UDP port

    def register_with_server(self, name: str):
        self.name = name
        tcp_handler.register_with_server(self.SERVER_IP, self.SERVER_TCP_PORT, self.name, self.CLIENT_IP, self.CLIENT_TCP_PORT, self.CLIENT_UDP_PORT)

    def deregister_with_server(self):
        tcp_handler.deregister_with_server(self.SERVER_IP, self.SERVER_TCP_PORT, self.name)

    def request_update(self):
        tcp_handler.request_update(self.SERVER_IP, self.SERVER_TCP_PORT, self.name, self.CLIENT_IP, self.CLIENT_TCP_PORT, self.CLIENT_UDP_PORT)

    def request_subjects_update(self, subjects_of_interest):
        tcp_handler.request_subjects_update(self.SERVER_IP, self.SERVER_TCP_PORT, self.name, *subjects_of_interest)

    def request_publish(self, subject, title, text):
        udp_handler.request_publish(self.udp_sock, self.SERVER_IP, self.SERVER_UDP_PORT, self.name, subject, title, text)

    def publish_comment(self, subject, title, text):
        udp_handler.publish_comment(self.udp_sock, self.SERVER_IP, self.SERVER_UDP_PORT, self.name, subject, title, text)


    # ========================================================================
    # TCP AND UDP MESSAGE HANDLING AND LISTENER METHODS BELOW
    # these methods are used in the main program in client_ui in their own threads to listen to incoming messages
    # ========================================================================
    def handle_tcp_message(self, client_socket, address):
        """This function acts as a dedicated worker for a single TCP connection."""
        print(f"[TCP] Connection established with {address}")
        try:
            # Pauses this specific thread and waits to receive up to 1024 bytes of data from the server
            data = client_socket.recv(1024)
            
            # If the server sent data (and didn't just instantly disconnect)
            if data:
                # Unpackages the raw bytes into a readable Python list
                parsed_msg = decode_msg(data)
                print(f"[TCP] Received: {parsed_msg}")
                
        finally:
            # TCP is a dedicated connection. Once the message is received, we MUST close the pipeline.
            client_socket.close()

    def handle_udp_message(self, data, address):
        """This function acts as a dedicated worker for a single UDP packet."""
        print(f"[UDP] Received from {address}: {data}")
        try:
            # Unpackages the raw bytes into a readable Python list
            parsed_msg = decode_msg(data)
            print(f"[UDP] Parsed message: {parsed_msg}")
            
        finally:
            # UDP is connectionless, so we don't have a pipeline to close. We just finish this function and wait for the next packet.
            pass

    # Start listening on TCP port for incoming messages from the server
    def start_tcp_listener(self):
        """This function sets up the TCP listener and loops forever."""
        # Creates a TCP socket (AF_INET = IPv4, SOCK_STREAM = TCP)
        client_tcp = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        client_tcp.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        
        # "Binds" (attaches) this socket to the client's IP address and TCP port
        client_tcp.bind((self.CLIENT_IP, self.CLIENT_TCP_PORT))
        
        # Tells the socket to start listening for incoming connections.
        # The '5' means it can hold up to 5 connections in a waiting room if the client gets too busy.
        client_tcp.listen(5)
        print(f"[CLIENT] TCP Listener started on {self.CLIENT_IP}:{self.CLIENT_TCP_PORT}")
        
        # An infinite loop to keep the TCP listener running forever
        while True:
            # accept() blocks (freezes) this thread until a connection comes in.
            # When it does, it returns a new, dedicated socket just for that connection, and the server's IP address.
            client_sock, addr = client_tcp.accept()
            
            # Instead of handling the message right here (which would block other connections),
            # we hire a new "worker" (a Thread) and hand them the client_sock to deal with in the background.
            message_thread = threading.Thread(target=self.handle_tcp_message, args=(client_sock, addr))
            
            # Starts the new background worker
            message_thread.start()

    # Start listening on UDP port for incoming messages from the server
    def start_udp_listener(self):
        """This function sets up the UDP listener and loops forever."""

        print(f"[CLIENT] Starting UDP listener on {self.CLIENT_IP}:{self.CLIENT_UDP_PORT}")
        
        # An infinite loop to catch incoming UDP packets
        while True:
            # recvfrom() freezes this thread until a UDP packet hits the port.
            # Because UDP is connectionless, it catches the raw 'data', and the 'addr' of whoever threw it.
            data, addr = self.udp_sock.recvfrom(1024)
            
            # Hire a new "worker" (a Thread) to handle this UDP message in the background.
            message_thread = threading.Thread(target=self.handle_udp_message, args=(data, addr))
            message_thread.start()

