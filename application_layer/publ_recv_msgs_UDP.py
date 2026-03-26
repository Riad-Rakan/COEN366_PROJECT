import time

from messages_defn import PUB, MESS, PUB_DEN, FORW

#used by clients
def build_publish_msg(name, subject, title, text):
    msg = []
    msg.append(PUB)             #message type
    msg.append(time.time())     #rq#, assume secs since epoch
    msg.append(name)            #name
    msg.append(subject)         #subject
    msg.append(title)           #title
    msg.append(text)            #text
    return msg

#used by servers
def build_pub_den_msg(rq, reason):
    msg = []
    msg.append(PUB_DEN)         #message type
    msg.append(rq)              #rq#
    msg.append(reason)          #reason
    return msg

def build_forward_msg(toserver, name, subject, title, text):
    msg = []
    if (toserver == True): msg.append(FORW)
    else: msg.append(MESS)      #message type
    msg.append(name)            #name
    msg.append(subject)         #subject
    msg.append(title)           #title
    msg.append(text)            #text
    return msg  

def build_forward_msg(toserver, payload):
    msg = []
    if (toserver == True): msg.append(FORW)
    else: msg.append(MESS)      #message type
    for p in payload:
        msg.append(p)
    return msg

def check_name_valid(payload, names):
    name = payload.pop(0)
    for n in names:
        if n == name: break
        else: return False
    return True

def check_subject_valid(payload, subjects):
    subject = payload.pop(0)
    for s in subjects:
        if s == subject: break
        else: return ""
    return subject

#maybe should be in server instead?
def handle_publish_request(payload, names, subjects):

    rq = payload.pop(0)

    #in case name does not exist, send denied message back to client
    if check_name_valid(payload, names) == False:
        reason = "Invalid name"
        return build_pub_den_msg(rq, reason)
    
    subject = check_subject_valid(payload, subjects)
    
    #in case subject does not exist, send denied message back to client
    if subject == "":
        reason = "Invalid name or subject"
        return build_pub_den_msg(rq, reason)
    
    #return message to forward to other servers and clients
    return build_forward_msg(True, payload), build_forward_msg(False, payload)