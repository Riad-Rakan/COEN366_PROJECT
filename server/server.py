import sys,socket,threading,json,os
sys.path.append("..")
from protocol import decode_msg, encode_msg                 

TCP_PORT = 10000 
UDP_PORT = 20000
HOST = '0.0.0.0' 

STORAGE_FILE = "storage.json"
registered_users = {} 

def load_data():
    global registered_users
    if os.path.exists(STORAGE_FILE):
        with open(STORAGE_FILE, "r") as f:
            registered_users = json.load(f)
            print(f"[SERVER] Loaded {len(registered_users)} users from database.")

def save_data():
    with open(STORAGE_FILE, "w") as f:
        json.dump(registered_users, f, indent=4)

def handle_tcp_client(client_socket, address):
    
    print(f"[TCP] Connection established with {address}")
    try:
        data = client_socket.recv(1024)
        
        if data:
            parsed_msg = decode_msg(data)
            print(f"[TCP] Received: {parsed_msg}")
            
            if parsed_msg[0] == "REGISTER":
                rq_num = parsed_msg[1]
                name = parsed_msg[2]

                registered_users[name] = {
                    "ip": parsed_msg[3],
                    "tcp_port": int(parsed_msg[4]),
                    "udp_port": int(parsed_msg[5]),
                    "interests": [] 
                }

                save_data()
                
                response = encode_msg("REGISTERED", rq_num)
                
                client_socket.send(response)
                print(f"[TCP] Sent confirmation for RQ#{rq_num}")

            if parsed_msg[0] == "DE-REGISTER":
                rq_num = parsed_msg[1]
                name = parsed_msg[2]

                if name in registered_users:
                    del registered_users[name] 
                    save_data()
                    print(f"[SERVER] User {name} deleted from database.")
                else:
                    print(f"[SERVER] User {name} not found. Ignored.")
                    
                print(f"[SERVER] User {name} deleted from database.")

    finally:
        client_socket.close()

def start_tcp_server():
    server_tcp = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    
    server_tcp.bind((HOST, TCP_PORT))
    server_tcp.listen(5)
    print(f"[SERVER] TCP Listening on port {TCP_PORT}")
    
    while True:
        client_sock, addr = server_tcp.accept()
        
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

if __name__ == "__main__":
    load_data()
    
    threading.Thread(target=start_tcp_server, daemon=True).start()
    threading.Thread(target=start_udp_server, daemon=True).start()
    input("[SERVER] Press Enter to shut down the server...\n")