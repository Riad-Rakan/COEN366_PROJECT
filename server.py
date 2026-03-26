from application_layer import publ_recv_msgs_UDP
from application_layer import messages_defn
from application_layer import comment_msgs_UDP

class server:
    def __init__(self):
        pass

    def receive_msg(self, payload):
        msg_type = payload.pop(0)
        

    def send_msg(self, client_addr, payload):
        pass
    