#!/usr/bin/env python

#BASED ON this great tutoril: https://realpython.com/python-sockets

import socket, selectors, types, sys, signal, struct, traceback, bullsandcows, communications

class ClientInfo():
    def __init__(self, ID, ADDRESS, ASOCK):
        self.id = ID
        self.address = ADDRESS
        self.asock = ASOCK
        self.isloged = False
        self.isplaying = False

    def play(self):
        self.isplaying = True

    def login(self, ID):
        self.id = ID
        self.isloged = True

class Server():
    def __init__(self, port):
        self.sel = selectors.DefaultSelector()
        # Number of clients
        self.clients = 0
        # Client info storage {socket_descriptor:(ID & ADDRESS)...}
        self.clientinfo = []
        #The message & Events
        self.events = None
        self.message = None
        # Passive socket creation
        self.psock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.psock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        try:
            self.psock.bind(('0.0.0.0', port))
        except socket.error as msg:
            print('Error: %s' % str(msg))
            sys.exit()
        self.psock.listen()
        self.psock.setblocking(False)
        self.sel.register(self.psock, selectors.EVENT_READ, data=None)
        # Handling signals
        signal.signal(signal.SIGINT, self.sighandler)

    def wrap_accept(self, sock):
        conn, addr = sock.accept()  # Should be ready to read
        conn.setblocking(False)
        self.message = communications.Message(self.sel, conn, addr)
        self.sel.register(conn, selectors.EVENT_READ | selectors.EVENT_WRITE, data=self.message)

    def sighandler(self, signum, frame):#Better than treat as a KeyboardInterrupt
        # Close all existing client sockets
        for key, mask in self.events:
            try:
                key.fileobject.close()
            except:
                print('Error: %s' % traceback.format_exc())
        #Close the listening socket
        self.sel.close()

    def serve(self):
        try:
            while True:
                self.events = self.sel.select(timeout=None)
                for key, mask in self.events:
                    if key.data is None:#The connection is from the psocket and has to be accepted
                        self.wrap_accept(key.fileobj)
                    else:#Already accepted connection, just copy the content
                        self.message = key.data
                        try:
                            self.message.process_events(mask)
                        except Exception as msg:
                            print('Error: %s' % str(msg))
                            self.message.close()
                        #Now Process messages

        except:#Unspected exception
            print('Error: %s' % traceback.format_exc())
            raise
        finally:
            self.sel.close()


if __name__ == '__main__':
    newServer = Server(8888)
    newServer.serve()
