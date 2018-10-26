import socket, select, sys, signal
from communication import send, receive, broadcast

class Server(object):

    def __init__(self, port=8085, backlog=5):
        # Number of clients
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
        for o in self.connectionlist:
            o.close()

        self.server.close()

    def getinfo(self, client):
        info = self.clientinfo[client]
        host, id = info[0][0], info[1]
        return '@'.join((id, host))

    def serve(self):
        inputs = [self.server, sys.stdin]
        self.outputs = []

        running = 1

        while running:
            try:
                inputready, outputready, exceptready = select.select(inputs, self.outputs, [])
            except:
                break

            for s in inputready:

                if s == self.server:
                    # handle the server socket
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
    ChatServer().serve()