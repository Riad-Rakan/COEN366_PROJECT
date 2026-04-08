# protocol.py

import socket

def get_my_ip():
    # gets ip address by connecting to an external address and checking the socket's own address.
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        s.connect(('10.255.255.255', 1)) 
        ip_address = s.getsockname()[0]
    except Exception:
        ip_address = '127.0.0.1' # Fallback just in case
    finally:
        s.close()
    return ip_address

def encode_msg(*args):
    # Takes arguments and turns them into a pipe-separated byte string, to be able to to be transmitted thorugh a socket
    message = " | ".join(str(arg) for arg in args)
    return message.encode('utf-8')

def decode_msg(byte_data):
    # Takes bytes from a socket and turns them into a list of strings.
    message = byte_data.decode('utf-8')
    return message.split(" | ")