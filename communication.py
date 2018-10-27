import pickle
import socket
import struct
import numpy as np

class Message():
    def __init__(self, messageID, messageType, fromID, toID, payload):
        self.mID = messageID
        self.mType = messageType
        self.fID = fromID
        self.tID = toID
        self.payload = payload

def login(client):

def send(channel, *args):
    buf = marshall(args)
    value = socket.htonl(len(buf))
    size = struct.pack("L", value)
    channel.send(size)
    channel.send(buf)

def receive(channel):
    size = struct.calcsize("L")
    size = channel.recv(size)
    try:
        size = socket.ntohl(struct.unpack("L", size)[0])
    except:
        return ''

    buf = ""

    while len(buf) < size:
        buf = channel.recv(size - len(buf))

    return unmarshall(buf)[0]