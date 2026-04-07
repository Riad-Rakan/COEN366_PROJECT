import sys,socket,threading,json,os
sys.path.append("..")
# Imports the built-in library for handling network connections
import socket 
# Imports the threading library so the server can do multiple things at exactly the same time
import threading 
# Imports your custom helper functions to convert bytes to strings and back
from protocol import decode_msg, encode_msg, get_my_ip
# Imports the json library (useful later for saving your users to the storage.json file)
import json 

class Server:

    # --- SERVER CONFIGURATION ---
    # The fixed port for all administrative "paperwork" (Registration, Updates, etc.)
    TCP_PORT = 10000 
    # The fixed port for blasting out and receiving the actual news broadcasts
    UDP_PORT = 20000 
    # '0.0.0.0' is a special address that tells the server to listen on ALL available network 
    # interfaces (Wi-Fi, Ethernet, localhost). This is required if other computers are connecting to it.
    HOST = '0.0.0.0' 

    other_server_ip = '127.0.0.1'  # Replace with the actual IP address of Server 2

    storage = json.load(open("storage.json", "r")) # Loads the storage.json file into a Python dictionary called 'storage'
    users = json.load(open("users.json", "r")) # Loads the users.json file into a Python dictionary called 'users'

    def __init__(self):
        self.udp_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.udp_socket.bind((self.CLIENT_IP, self.CLIENT_UDP_PORT))

    # ========================================================================
    # JSON File I/O Helper Methods
    # ========================================================================
    def load_users(self):
        """Load users data from users.json"""
        with open("users.json", "r") as f:
            return json.load(f)

    def save_users(self):
        """Save users data to users.json"""
        with open("users.json", "w") as f:
            json.dump(self.users, f, indent=4)

    def load_storage(self):
        """Load storage data from storage.json"""
        with open("storage.json", "r") as f:
            return json.load(f)

    def save_storage(self):
        """Save storage data to storage.json"""
        with open("storage.json", "w") as f:
            json.dump(self.storage, f, indent=4)


    # ========================================================================
    # TCP/UDP Server Methods
    # ========================================================================
    def handle_tcp_client(self, client_socket, address):
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
                    self.handle_registration_request(client_socket, parsed_msg)
                elif parsed_msg[0] == "DE-REGISTER":
                    self.handle_deregistration_request(client_socket, parsed_msg)
                elif parsed_msg[0] == 'UPDATE':
                    self.handle_update_request(client_socket, parsed_msg)
                elif parsed_msg[0] == 'SUBJECTS':
                    self.handle_subjects_request(client_socket, parsed_msg)
                    
        finally:
            # TCP is a dedicated connection. Once the request is handled, we MUST close the pipeline.
            client_socket.close()

    def handle_udp_client(self, data, address):
        """This function acts as a dedicated worker for a single UDP packet."""
        print(f"[UDP] Received from {address}: {data}")
        try:
            # Unpackages the raw bytes into a readable Python list (e.g., ['PUBLISH', '1', 'User1', ...])
            parsed_msg = decode_msg(data)
            print(f"[UDP] Parsed message: {parsed_msg}")
            
            # Checks if the first word in the message is the publish command
            if parsed_msg[0] == "PUBLISH":
                self.handle_publish_request(address, parsed_msg)
            elif parsed_msg[0] == "FORWARD":
                self.forward_publish_to_clients(parsed_msg[1], parsed_msg[2], parsed_msg[3], parsed_msg[4])
            elif parsed_msg[0] == "PUBLISH-COMMENT":
                self.handle_comment_request(address, parsed_msg)
        finally:
            # UDP is connectionless, so we don't have a pipeline to close. We just finish this function and wait for the next packet.
            pass

    def start_tcp_server(self):
        """This function sets up the TCP receptionist and loops forever."""
        # Creates a TCP socket (AF_INET = IPv4, SOCK_STREAM = TCP)
        server_tcp = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        
        # "Binds" (attaches) this socket to the computer's IP address and the designated TCP port
        server_tcp.bind((self.HOST, self.TCP_PORT))
        
        # Tells the socket to start listening for incoming connections. 
        # The '5' means it can hold up to 5 users in a waiting room if the server gets too busy.
        server_tcp.listen(5)
        print(f"[SERVER] TCP Listening on port {self.TCP_PORT}")
        
        # An infinite loop to keep the receptionist at the desk forever
        while True:
            # accept() blocks (freezes) this thread until a client actually connects.
            # When they do, it returns a new, dedicated socket just for them, and their IP address.
            client_sock, addr = server_tcp.accept()
            
            # Instead of handling the client right here (which would block other users from connecting),
            # we hire a new "worker" (a Thread) and hand them the client_sock to deal with in the background.
            client_thread = threading.Thread(target=self.handle_tcp_client, args=(client_sock, addr))
            
            # Starts the new background worker
            client_thread.start()

    def start_udp_server(self):
        """This function sets up the UDP receptionist and loops forever."""
        print(f"[SERVER] UDP Listening on port {self.UDP_PORT}")
        
        # An infinite loop to catch flying packets
        while True:
            # recvfrom() freezes this thread until a UDP packet hits the port.
            # Because UDP is connectionless, it catches the raw 'data', and the 'addr' of whoever threw it.
            data, addr = self.udp_socket.recvfrom(1024)
            
            client_thread = threading.Thread(target=self.handle_udp_client, args=(data, addr))
            client_thread.start()


    # ========================================================================
    # 2.1 Registration (over TCP)
    # ========================================================================
    def handle_registration_request(self, client_socket, parsed_msg):
        # Grabs the Request Number (RQ#) from the list
        rq_num = parsed_msg[1]
        
        # Extracts the client information from the registration message
        # Format: REGISTER | RQ# | Name | IP Address | TCP Socket# | UDP Socket#
        client_name = parsed_msg[2]
        client_ip = parsed_msg[3]
        client_tcp_port = int(parsed_msg[4])
        client_udp_port = int(parsed_msg[5])
        
        # Adds the client information to the users dictionary
        # New clients start with an empty interests list
        self.users[client_name] = {
            "ip": client_ip,
            "tcp_port": client_tcp_port,
            "udp_port": client_udp_port,
            "interests": []
        }
        
        # Saves the updated users dictionary to users.json
        self.save_users()
        
        print(f"[TCP] Registered user: {client_name} at {client_ip}:{client_udp_port}")
        
        # Packages the success reply: REGISTERED | RQ#
        response = encode_msg("REGISTERED", rq_num)
        
        # Sends the packaged reply back down the active TCP pipeline to the client
        client_socket.send(response)
        print(f"[TCP] Sent confirmation for RQ#{rq_num}")


    # ========================================================================
    # 2.2 Deregistration (over TCP)
    # ========================================================================
    def handle_deregistration_request(self, client_socket, parsed_msg):
        # Grabs the Request Number (RQ#) from the list
        # note that this isn't used to send a reply as per requirements
        rq_num = parsed_msg[1]

        client_name = parsed_msg[2]

        if client_name in self.users:
            del self.users[client_name]
            self.save_users()
            print(f"[TCP] Deregistered user: {client_name}")
        else:
            print(f"[TCP] Deregistration failed: User {client_name} not found.")
    

    # ========================================================================
    # 2.3 Users updating their information (over TCP)
    # ========================================================================
    def handle_update_request(self, client_socket, parsed_msg):
        # Grabs the Request Number (RQ#) from the list
        rq_num = parsed_msg[1]

        # Extracts client information from update message
        # Format: UPDATE | RQ# | Name | IP Address | TCP Socket# | UDP Socket#
        client_name = parsed_msg[2]
        client_ip = parsed_msg[3]            

        # Verify that ports are numbers
        try:
            client_tcp_port = int(parsed_msg[4])
            client_udp_port = int(parsed_msg[5])
        except ValueError:
            response = encode_msg("UPDATE-DENIED", rq_num, "Ports must be numbers")
            client_socket.send(response)
            print(f"[TCP] Sent UPDATE-DENIED for RQ#{rq_num}: Ports must be numbers")
            return

        # Verify that ports are in a valid range
        if not (1 <= client_tcp_port <= 65535) or not (1 <= client_udp_port <= 65535):
            response = encode_msg("UPDATE-DENIED", rq_num, "Ports must be within valid range (1-65535)")
            client_socket.send(response)
            print(f"[TCP] Sent UPDATE-DENIED for RQ#{rq_num}: Ports must be within valid range (1-65535)")
            return

        # Verify that user is registered
        if client_name not in self.users:
            response = encode_msg("UPDATE-DENIED", rq_num, f"User: {client_name} not registered")
            client_socket.send(response)
            print(f"[TCP] Sent UPDATE-DENIED for RQ#{rq_num}: User: {client_name} not registered")
            return

        # Updates user dictionary with new client information
        client_interests = self.users[client_name].get("interests", [])
        self.users[client_name] = {
            "ip":client_ip,
            "tcp_port": client_tcp_port,
            "udp_port": client_udp_port,
            "interests": client_interests
        }

        # Saves the updated dictionary to storable .json
        self.save_users()
        
        print(f"[TCP] Updated user: {client_name} to {client_ip}:{client_udp_port} with TCP port {client_tcp_port}")

        # Packages success response with format: UPDATE-CONFIRMED | RQ# | Name | IP Address | TCP Socket# | UDP Socket#
        response = encode_msg("UPDATE-CONFIRMED", rq_num, client_name, client_ip, client_tcp_port, client_udp_port)

        # Sends packaged response down the active TCP pipeline to the user
        client_socket.send(response)
        print(f"[TCP] Sent confirmation for RQ#{rq_num}")


    # ========================================================================
    # 2.4 Users updating their subjects of interest (over TCP)
    # ========================================================================
    def handle_subjects_request(self, client_socket, parsed_msg):
        # Grabs the Request Number (RQ#) from the list
        rq_num = parsed_msg[1]

        # Extracts client information from update message
        # Format: SUBJECTS | RQ# | Name | List of Subjects
        client_name = parsed_msg[2]
        client_interests = parsed_msg[3:]

        # Verify that the subjects list is not empty
        if not client_interests:
            response = encode_msg("SUBJECTS-REJECTED", rq_num, "Subject list is empty.")
            client_socket.send(response)
            print(f"[TCP] Sent SUBJECTS-REJECTED for RQ#{rq_num}: Subject list is empty.")
            return

        # Verify user is registered
        elif client_name not in self.users:
            response = encode_msg("SUBJECTS-REJECTED", rq_num, "User is not registered.")
            client_socket.send(response)
            print(f"[TCP] Sent SUBJECTS-REJECTED for RQ#{rq_num}: User: {client_name} not registered")
            return

        # Verify that subject is a valid subject category from the storage.json subject list
        invalid_subjects = []
        for subject in client_interests:
            if subject not in self.storage:
                invalid_subjects.append(subject)
        if invalid_subjects:
            response = encode_msg("SUBJECTS-REJECTED", rq_num, f"Invalid subjects: {', '.join(invalid_subjects)}")
            client_socket.send(response)
            print(f"[TCP] Sent SUBJECTS-REJECTED for RQ#{rq_num}: Invalid subjects: {', '.join(invalid_subjects)}")
            return
        
        else:
            self.users[client_name]["interests"] = list(set(client_interests))

            # Saves the updated dictionary to storable .json
            self.save_users()

            print(f"[TCP] Updated subjects of interest for {client_name}: {client_interests}")

            # Packages success response with format: UPDATE-CONFIRMED | RQ# | Name | IP Address | TCP Socket# | UDP Socket#
            response = encode_msg("SUBJECTS-UPDATED", rq_num, client_name, client_interests)

            # Sends packaged response down the active TCP pipeline to the user
            client_socket.send(response)
            print(f"[TCP] Sent confirmation for RQ#{rq_num}")


    # ========================================================================
    # 2.5 Users publishing and receiving messages on subjects of interest (over UDP)
    # ========================================================================
    def handle_publish_request(self, address, parsed_msg):
        # Grabs the Request Number (RQ#) from the list
        rq_num = parsed_msg[1]

        name = parsed_msg[2]
        requested_subject = parsed_msg[3]
        title = parsed_msg[4]
        text = parsed_msg[5]

        name_valid = False
        subject_valid = False

        subject_valid = requested_subject in self.storage

        if not name_valid:
            response = encode_msg("PUBLISH-DENIED", rq_num, "Invalid Name")
            self.udp_socket.sendto(response, address)
            print(f"[UDP] Sent PUBLISH-DENIED for RQ#{rq_num}: Invalid Name")
            return
        
        if not subject_valid:
            response = encode_msg("PUBLISH-DENIED", rq_num, "Invalid Subject")
            self.udp_socket.sendto(response, address)
            print(f"[UDP] Sent PUBLISH-DENIED for RQ#{rq_num}: Invalid Subject")
            return
        
        self.forward_publish_to_clients(name, requested_subject, title, text)   # article gets saved in here
        self.forward_publish_to_servers(name, requested_subject, title, text)
        print(f"[UDP] Successfully handled PUBLISH request for RQ#{rq_num}. Forwarded to clients and servers.")
        
    def forward_publish_to_clients(self, name, subject, title, text):

        # Save article using title as the article key. No need to check the input since it was already validated from handle_publish_request
        if title in self.storage[subject]:
            print(f"[UDP] Duplicate article title detected for subject '{subject}'. Overwriting existing article.")
        self.storage[subject][title] = {
            "text": text,
            "comments": {}
        }
        self.save_storage()

        # This function will be responsible for blasting the news out to all interested users over UDP.
        response = encode_msg("MESSAGE", name, subject, title, text)
        for user in self.users:
            if subject in self.users[user]["interests"]:
                user_ip = self.users[user]["ip"]
                user_udp_port = self.users[user]["udp_port"]
                self.udp_socket.sendto(response, (user_ip, user_udp_port))
                print(f"[UDP] Forwarded message to {user} at {user_ip}:{user_udp_port}")

    def forward_publish_to_servers(self, name, subject, title, text):
        # This function will be responsible for forwarding the news to other servers over UDP.
        response = encode_msg("FORWARD", name, subject, title, text)
        if self.other_server_ip != '127.0.0.1': self.udp_socket.sendto(response, (self.other_server_ip, self.UDP_PORT)) #only send if there is a second server which is not localhost
        print(f"[UDP] Forwarded message to Server 2 at {self.other_server_ip}:{self.UDP_PORT}")


    # ========================================================================
    # 2.6 Commenting messages (over UDP)
    # ========================================================================
    def handle_comment_request(self, address, parsed_msg):

        subject = parsed_msg[2]
        title = parsed_msg[3]
        commenter = parsed_msg[1]
        comment_text = parsed_msg[4]

        if subject not in self.storage or title not in self.storage[subject]:
            print(f"[UDP] Article not found for comment. Ignoring.")
            return

        article = self.storage[subject][title]
        if "comments" not in article or not isinstance(article["comments"], list):
            article["comments"] = []

        # Check for duplicate comment (same commenter and same text)
        for comment in article["comments"]:
            if comment["commenter"] == commenter and comment["text"] == comment_text:
                print(f"[UDP] Duplicate comment detected. Ignoring.")
                return

        article["comments"].append({"commenter": commenter, "text": comment_text})
        self.save_storage()

        # Forward to other server if sender was a client. Since all servers have the same port, we can check it to determine if the sender was a server.
        if address[1] != self.UDP_PORT:
            self.forward_publish_comment_to_servers(parsed_msg)
        self.forward_publish_comment_to_clients(commenter, subject, title, comment_text)

    #PUBLISH-COMMENT is common between client->server and server->server, but client is the one who creates the encoded message.
    def forward_publish_comment_to_servers(self, parsed_msg):
        # This function will be responsible for forwarding the comment to other servers over UDP.
        encoded_data = encode_msg(parsed_msg[0], parsed_msg[1], parsed_msg[2], parsed_msg[3], parsed_msg[4])
        if self.other_server_ip != '127.0.0.1': self.udp_socket.sendto(encoded_data, (self.other_server_ip, self.UDP_PORT)) #only send if there is a second server which is not localhost
        print(f"[UDP] Forwarded comment to Server 2 at {self.other_server_ip}:{self.UDP_PORT}")

    def forward_publish_comment_to_clients(self, name, subject, title, text):
        # This function will be responsible for blasting the comment out to all interested users over UDP.
        response = encode_msg("MESSAGE-COMMENT", name, subject, title, text)
        for user in self.users:
            if subject in self.users[user]["interests"]:
                user_ip = self.users[user]["ip"]
                user_udp_port = self.users[user]["udp_port"]
                self.udp_socket.sendto(response, (user_ip, user_udp_port))
                print(f"[UDP] Forwarded comment to {user} at {user_ip}:{user_udp_port}")
                


                
# The guard block: only runs this startup sequence if you run server.py directly
if __name__ == "__main__":

    svr: Server = Server()

    print("[SERVER] Server IP Address:", get_my_ip())

    other_ip = input("Enter the IP address of the other server (or press Enter if no other server): ")
    svr.other_server_ip = other_ip if other_ip != "" else '127.0.01'
    
    # We want both the TCP and UDP servers to run simultaneously without blocking each other.
    # So, we launch the TCP server loop in its own background thread.
    # daemon=True means this thread will automatically be killed if we close the main program.
    threading.Thread(target=svr.start_tcp_server, daemon=True).start()
    
    # We launch the UDP server loop in a second background thread.
    threading.Thread(target=svr.start_udp_server, daemon=True).start()
    
    # The two threads above are running in the background, so the main program needs a way to stay open.
    # This input() function simply pauses the main script until you press the Enter key in the terminal.
    input("[SERVER] Press Enter to shut down the server...\n")