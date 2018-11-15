#!/usr/bin/env python

import bullsandcows, communications, socket, selectors, types, sys, signal, struct

class Server():
    def __init__(self, port):
        self.sel = selectors.DefaultSelector()
        # Number of clients
        self.clients = 0
        # Client info storage {socket_descriptor:(ID & ADDRESS)...}
        self.clientinfo = {}
        # For the socket descriptors
        self.connectionlist = []
        # Passive socket creation
        self.psock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.psock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.psock.bind(('0.0.0.0', port))
        self.psock.listen()
        self.psock.setblocking(False)
        self.sel.register(self.psock, selectors.EVENT_READ, data=None)
        #print('Listening to port', port, '...')
        # Handling signals
        signal.signal(signal.SIGINT, self.sighandler)

    def accept_wrapper(self, sock):
        conn, addr = sock.accept()  # Should be ready to read
        print("accepted connection from", addr)
        conn.setblocking(False)
        message = communications.Comunication(self.sel, conn, addr)
        self.sel.register(conn, selectors.EVENT_READ | selectors.EVENT_WRITE, data=message)

    def sighandler(self, signum, frame):
        # Close all existing client sockets
        for asocket in self.events:
            try:
                asocket.fileobject.close()

        self.psock.close()

    def serve(self):
        try:
            while True:
                self.events = self.sel.select(timeout=None)
                for key, mask in self.events:
                    if key.data is None:
                        self.accept_wrapper(key.fileobj)
                    else:
                        message = key.data
                        try:
                            message.process_events(mask)
                        except Exception:
                            message.close()

        finally:
            self.sel.close()


if __name__ == "__main__":
    #newServer = Server(8888, 100)
    #newServer.serve()
    print(communications.MESSAGE.GUESS)
    communications.MESSAGE.GUESS = 15
    r = struct.pack('!ihiih',33,25,56,1,6566)
    print(len(r))
    if len(r) == 14:
        mId, mType, mFrom, mTo = struct.unpack('!ihii',r)
    else:
        mId, mType, mFrom, mTo, mPayload = struct.unpack('!ihiih', r)
    print('Ox%X' % mPayload)