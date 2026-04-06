import socket
import random
from protocol import encode_msg, decode_msg

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
    
