#!/usr/bin/env python

import random, string, socket, select, sys, signal, numpy as np
#from communication import send, receive

#Constants
LOGIN = 0x01
LOGINACK = 0x11
ID_OK = 0x00
ID_USED = 0x11
ID_OUTOFRANGE = 0x12
ERROR = 0x13

NEWGAME = 0x02
NEWGAMEACK = 0x12

GUESS = 0x03
GUESSACK = 0x13

QUIT = 0x04
QUITACK = 0x14
QUIT_OK = 0x00
ERROR = 0x13

class Message():
    def __init__(self, messageID, messageType, fromID, toID, payload):
        self.mID = messageID
        self.mType = messageType
        self.fID = fromID
        self.tID = toID
        self.payload = payload

class BullsAndCows():
    def __init__(self):
        self.secret = ''.join(random.choice(string.digits)for _ in range(4))

class Server():
    def __init__(self, port=8085, backlog=5):
        # Number of clients
        self.id = 0
        self.clients = 0
        # Client info storage
        self.clientinfo = {}
        # For the socket descriptors
        self.connectionlist = []
        # Passive socket creation
        self.server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.server.bind(("0.0.0.0", port))
        self.server.listen(backlog)
        #print('Listening to port', port, '...')
        # Handling signals
        signal.signal(signal.SIGINT, self.sighandler)

    def sighandler(self, signum, frame):
        #print('Shutting down server...')
        # Close all existing client sockets
        for aux in self.connectionlist:
            aux.close()

        self.server.close()

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

    def login(self, client):
        info = self.clientinfo[client]
        host, id = info[0][0], info[1]
        return '@'.join((id, host))

    def loginack(self, client):
        r=3

    def newgame(self, client):
        r=3

    def newgameack(self, client):
        r=3

    def guess(self, client):
        r=3

    def guessack(self, client):
        r=3

    def quit(self, client):
        r=3

    def quitack(self, client):
        r=3

    def play(self):
        inputs = [self.server, sys.stdin]
        self.outputs = []

        running = 1

        while running:
            try:
                infds, outfds, errfds = select.select(inputs, self.outputs, [])
            except:
                break

            for s in infds:

                if s == self.server:
                    # Server socket
                    client, address = self.server.accept()
                    print('chatserver: got connection %d from %s' % (client.fileno(), address))
                    # Read the login name
                    cname = receive(client).split('NAME: ')[1]

                    # Compute client name and send back
                    self.clients += 1
                    send(client, 'CLIENT: ' + str(address[0]))
                    inputs.append(client)

                    self.clientmap[client] = (address, cname)
                    # Send joining information to other clients
                    msg = '\n(Connected: New client (%d) from %s)' % (self.clients, self.getname(client))
                    for o in self.outputs:
                        # o.send(msg)
                        send(o, msg)

                    self.outputs.append(client)

                elif s == sys.stdin:
                    # handle standard input
                    junk = sys.stdin.readline()
                    running = 0
                else:
                    # handle all other sockets
                    try:
                        # data = s.recv(BUFSIZ)
                        data = receive(s)
                        if data:
                            # Send as new client's message...
                            msg = '\n#[' + self.getname(s) + ']>> ' + data
                            # Send data to all except ourselves
                            for o in self.outputs:
                                if o != s:
                                    # o.send(msg)
                                    send(o, msg)
                        else:
                            print('chatserver: %d hung up' % s.fileno())
                            self.clients -= 1
                            s.close()
                            inputs.remove(s)
                            self.outputs.remove(s)

                            # Send client leaving information to others
                            msg = '\n(Hung up: Client from %s)' % self.getname(s)
                            for o in self.outputs:
                                # o.send(msg)
                                send(o, msg)

                    except:
                        # Remove
                        inputs.remove(s)
                        self.outputs.remove(s)

        self.server.close()


if __name__ == "__main__":
    #ChatServer().serve()
    r=3