from messages_defn import PUB_COMM, COMM

#used by clients -> servers or servers -> servers
def build_pub_comm_msg(name, subject, title, text):
    msg = []
    msg.append(PUB_COMM)        #message type
    msg.append(name)            #name
    msg.append(subject)         #subject
    msg.append(title)           #title
    msg.append(text)            #text
    return msg

#used by servers -> clients
def build_comm_msg(name, subject, title, text):
    msg = []
    msg.append(COMM)            #message type
    msg.append(name)            #name
    msg.append(subject)         #subject
    msg.append(title)           #title
    msg.append(text)            #text
    return msg

def handle_comment_request(payload):
    msg = []
    msg.append(COMM)            #message type
    for p in payload:
        msg.append(p)
    return msg