import socket
import random
from protocol import encode_msg, decode_msg

# ========================================================================
# 2.1 Registration (over TCP)
# ========================================================================
def register_with_server(server_ip, server_tcp_port, client_name, client_ip, client_tcp_port, client_udp_port):
                                                        # (client_tcp) is a new socket object (AF_INET) -> IPV4 | (SOCK_STREAM) -> TCP
    client_tcp = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    try:                                                
        print(f"[CLIENT] Connecting to Server at {server_ip}:{server_tcp_port}...")
        client_tcp.connect((server_ip,server_tcp_port)) # Attemps to establish TCP conextion handshake with the server
        rq_num = random.randint(0, 200)                 # generate a request #
                                                        # Format : [ REGISTER | RQ# | Name | IP Address | TCP Spcket# | UDP Socket# ]
        message_bytes = encode_msg("REGISTER", rq_num, client_name, client_ip, client_tcp_port, client_udp_port)
        print("[CLIENT] Sending reg. request ...")      # This ofcourse only runs if it passes the ".connect() from earlier"
        client_tcp.send(message_bytes)                        # send the message
        answer = client_tcp.recv(1024)                  # Receive the answer -> 1024 bytes is the max size to receive
        answer_parsed = decode_msg(answer)              # decode the message we get from the server
        
        print(f"[CLIENT] Server replied: {answer_parsed}")
    except ConnectionRefusedError:                      # This error is cached by the client but thrown by | "client_tcp.connect( ... )"
        print("[CLIENT] Connection failed. Is server running?")
    finally:                                            # In all cases, close the TCP link
        client_tcp.close()

# ========================================================================
# 2.2 Deregistration (over TCP)
# ========================================================================
def deregister_with_server(server_ip, server_tcp_port, client_name):
    client_tcp = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    try:                                                
        print(f"[CLIENT] Connecting to Server at {server_ip}:{server_tcp_port}...")
        client_tcp.connect((server_ip,server_tcp_port)) # Attemps to establish TCP conextion handshake with the server
        rq_num = random.randint(0, 200)                 # generate a request #
                                                        # Format : [ DE-REGISTER | RQ# | Name ]
        message_bytes = encode_msg("DE-REGISTER", rq_num, client_name)
        print("[CLIENT] Sending de-reg. request ...")   # This ofcourse only runs if it passes the ".connect() from earlier"
        client_tcp.send(message_bytes)                  # send the message

    except ConnectionRefusedError:                      # This error is cached by the client but thrown by | "client_tcp.connect( ... )"
        print("[CLIENT] Connection failed. Is server running?")
    finally:                                            # In all cases, close the TCP link
        client_tcp.close()

# ========================================================================
# 2.3. Users updating their information (over TCP)
# ========================================================================
def request_update(server_ip, server_tcp_port, client_name, client_ip, client_tcp_port, client_udp_port):
    rq_num = random.randint(0, 200) # Generates a random Request Number (RQ#) to track this specific publish attempt

    # Packages the variables into a pipe-separated byte string using helper method from protocol method.
    # Format: UPDATE | RQ# | Name | IP Address | TCP Socket# | UDP Socket#
    msg_bytes = encode_msg("UPDATE", rq_num, client_name, client_ip, client_tcp_port, client_udp_port)
    print(f"[CLIENT] Sending UPDATE request for RQ#{rq_num} over TCP...")
    # Creates a new socket object connecting to server IPv4 address over TCP
    # Sends the packaged byte string through this connection
    client_tcp = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    client_tcp.connect((server_ip, server_tcp_port))
    client_tcp.send(msg_bytes)

    answer = client_tcp.recv(1024)                  # Receive the answer -> 1024 bytes is the max size to receive
    answer_parsed = decode_msg(answer)              # decode the message we get from the server
        
    print(f"[CLIENT] Server replied: {answer_parsed}")

    
# ========================================================================
# 2.4. Users updating their subjects of interest (over TCP)
# ========================================================================
def request_subjects_update(server_ip, server_tcp_port, client_name, subject_list):
    rq_num = random.randint(0, 200) # Generates a random Request Number (RQ#) to track this specific publish attempt

    # Packages the variables into a pipe-separated byte string using helper method from protocol method.
    # Format: SUBJECTS | RQ# | Name | List of Subjects
    msg_bytes = encode_msg("SUBJECTS", rq_num, client_name, *subject_list)
    print(f"[CLIENT] Sending SUBJECTS request for RQ#{rq_num} over TCP...")
    # Creates a new socket object connecting to server IPv4 address over TCP
    # Sends the packaged byte string through this connection
    client_tcp = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    client_tcp.connect((server_ip, server_tcp_port))
    client_tcp.send(msg_bytes)
        
    answer = client_tcp.recv(1024)                  # Receive the answer -> 1024 bytes is the max size to receive
    answer_parsed = decode_msg(answer)              # decode the message we get from the server
        
    print(f"[CLIENT] Server replied: {answer_parsed}")