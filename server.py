#!/usr/bin/env python

import bullsandcows, communications, socket, select, sys, signal, struct#, numpy as np

class Message():
    def __init__(self, messageID, messageType, fromID, toID, payload):
        self.mID = messageID
        self.mType = messageType
        self.fID = fromID
        self.tID = toID
        self.payload = payload

class Server():
    def __init__(self, port, backlog):
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

    def serve(self):
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
    #newServer = Server(8888, 100)
    #newServer.serve()
    r = b'\xff\x00\x00\x00\x07\x00\x00\x00@\x00\x00\x00\xff\x03\x00\x00Hola'
    mId, mType, mFrom, mTo, mPayload = struct.unpack('ihii'+str(len(r)-16)+'s', r)
    print(mPayload)