# protocol.py

import socket

def get_my_ip():
    """Opens a dummy connection to figure out the computer's local network IP."""
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        # It doesn't actually send data, just uses the routing table to find the local IP
        s.connect(('10.255.255.255', 1)) 
        ip_address = s.getsockname()[0]
    except Exception:
        ip_address = '127.0.0.1' # Fallback just in case
    finally:
        s.close()
    return ip_address

# Now you can set it dynamically!
CLIENT_IP = get_my_ip()
print(f"My Client IP is automatically set to: {CLIENT_IP}")

def encode_msg(*args):
    """Takes arguments and turns them into a pipe-separated byte string, to be able to to be transmitted thorugh a socket"""
    # Example: encode_msg("REGISTER", "1", "Alice", "192.168.1.15", 5000, 6000)
    message = " | ".join(str(arg) for arg in args)
    return message.encode('utf-8')

def decode_msg(byte_data):
    """Takes bytes from a socket and turns them into a list of strings."""
    # Example returns: ['REGISTER', '1', 'Alice', '192.168.1.15', '5000', '6000']
    message = byte_data.decode('utf-8')
    return message.split(" | ")