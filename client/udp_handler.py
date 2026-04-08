import random
import socket

from protocol import encode_msg

# ========================================================================
# 2.5. Users publishing and receiving messages on subjects of interest (over UDP)
# ========================================================================
def request_publish(udpsock, server_ip, server_tcp_port, name, subject, title, text):
    rq_num = random.randint(0, 200) # Generates a random Request Number (RQ#) to track this specific publish attempt

    # Format: PUBLISH | RQ# | Name | Subject | Title | Text
    msg_bytes = encode_msg("PUBLISH", rq_num, name, subject, title, text)
    print(f"[CLIENT] Sending PUBLISH request for RQ#{rq_num} over UDP...")
    # Sends the packaged byte string over UDP to the server's IP and UDP port
    udpsock.sendto(msg_bytes, (server_ip, server_tcp_port))


# ========================================================================
# 2.6 Commenting messages (over UDP)
# ========================================================================
#Publish Comment is created by a client and sent to server. This will be forwarded to the other server as-is
def publish_comment(udpsock, server_ip, server_tcp_port, name, subject, title, text):

    # Format: PUBLISH-COMMENT | RQ# | Name | Subject | Title | Text
    msg_bytes = encode_msg("PUBLISH-COMMENT", name, subject, title, text)
    print(f"[CLIENT] Sending PUBLISH-COMMENT request...")
    # Sends the packaged byte string over UDP to the server's IP and UDP port
    udpsock.sendto(msg_bytes, (server_ip, server_tcp_port))
