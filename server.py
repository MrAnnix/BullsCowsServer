#!/usr/bin/env python

import bullsandcows, communications, socket, selectors, types, sys, signal, struct

class Server():
    def __init__(self, port, backlog):
        self.sel = selectors.DefaultSelector()
        # Number of clients
        self.id = 0
        self.clients = 0
        # Client info storage
        self.clientinfo = {}
        # For the socket descriptors
        self.connectionlist = []
        # Passive socket creation
        self.psock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.psock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.psock.bind(("0.0.0.0", port))
        self.psock.listen(backlog)
        self.psock.setblocking(False)
        self.sel.register(self.psock, selectors.EVENT_READ, data=None)
        #print('Listening to port', port, '...')
        # Handling signals
        signal.signal(signal.SIGINT, self.sighandler)

    def accept_wrapper(self, sock):
        conn, addr = sock.accept()  # Should be ready to read
        print("accepted connection from", addr)
        conn.setblocking(False)
        message = communications.Communication(self.sel, conn, addr)
        self.sel.register(conn, selectors.EVENT_READ, data=message)

    def sighandler(self, signum, frame):
        #print('Shutting down server...')
        # Close all existing client sockets
        for aux in self.connectionlist:
            aux.close()

        self.server.close()

    def serve(self):
        try:
            while True:
                events = self.sel.select(timeout=None)
                for key, mask in events:
                    if key.data is None:
                        self.accept_wrapper(key.fileobj)
                    else:
                        message = key.data
                        try:
                            message.process_events(mask)
                        except Exception:
                            print(
                                "main: error: exception for",
                                #f"{message.addr}:\n{traceback.format_exc()}",
                            )
                            message.close()
        except KeyboardInterrupt:
            print("caught keyboard interrupt, exiting")
        finally:
            self.sel.close()


if __name__ == "__main__":
    #newServer = Server(8888, 100)
    #newServer.serve()
    r = b'x\x00\x00\x00x\x00\x00\x00x\x00\x00\x00x\x00\x00\x00Hola'
    print(len(r))
    mId, mType, mFrom, mTo, mPayload = struct.unpack('ihii'+str(len(r)-16)+'s', r)
    print(mPayload)