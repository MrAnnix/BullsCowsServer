#!/usr/bin/env python

#BASED ON this great tutoril: https://realpython.com/python-sockets

import socket, selectors, types, sys, signal, struct, traceback, communications, bullsandcows

#We have to avoid constant changes
def constant(f):
    def fset(self, value):
        raise TypeError
    def fget(self):
        return f()
    return property(fget, fset)

class _Constants():
    # Constants
    @constant
    def LOGIN():
        return 0x01

    @constant
    def LOGINACK():
        return 0x11

    @constant
    def ID_OK():
        return 0x00

    @constant
    def ID_USED():
        return 0x11

    @constant
    def ID_OUTOFRANGE():
        return 0x12

    @constant
    def ERROR():
        return 0x13

    @constant
    def NEWGAME():
        return 0x02

    @constant
    def NEWGAMEACK():
        return 0x12

    @constant
    def GAME_OK():
        return 0x00

    @constant
    def LENGTHOUTOFRANGE():
        return 0x12

    @constant
    def GUESS():
        return 0x03

    @constant
    def GUESSACK():
        return 0x13

    @constant
    def QUIT():
        return 0x04

    @constant
    def QUITACK():
        return 0x14

    @constant
    def QUIT_OK():
        return 0x00

MESSAGE = _Constants()

class ClientErr(Exception):
    pass

class ClientInfo():
    id = None
    address = None
    asock = None
    game = None
    length = 0

    def newgame(self, size):
        if self.game is None:
            self.game = bullsandcows.BullsAndCows(size)
            self.length = size
            print('Client with id %i has started a new game' % self.id)
        else:
            raise ClientErr('Cannot play: Client with ID: %i, is already playing' % self.id)

    def guessgame(self, guess):
        if self.game is None:
            raise ClientErr('Cannot guess:Client with id %i is not playing' % self.id)
        return self.game.compare(str(guess).zfill(self.length))

    def login(self, ID, addr, sock):
        if self.id is None:
            self.id = ID
            self.address = addr
            self.asock = sock
            print('Client with id %i has loged in' % ID)
        else:
            raise ClientErr('Cannot login: Client with ID %i, is already loged in' % id)

class Server():
    def __init__(self, port):
        self.sel = selectors.DefaultSelector()
        # Client info storage
        self.clients = []
        #The message temporary variable
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
        events = selectors.EVENT_READ | selectors.EVENT_WRITE
        self.sel.register(conn, events, data=self.message)

    def sighandler(self, signum, frame):#Better than treat as a KeyboardInterrupt
        # Close all existing client sockets
        for key, mask in self.events:
            try:
                key.fileobject.close()
            except:
                print('Error: %s' % traceback.format_exc())
        #Close the listening socket
        self.sel.close()

    def process_msg(self):
        mymsg = self.message
        if mymsg.mType == MESSAGE.LOGIN:
            if (mymsg.fID == 0) or (mymsg.fID > 200):
                self.loginERR(True)
                return
            newclient = ClientInfo()
            newclient.login(mymsg.fID, mymsg.addr, mymsg.sock)
            if self.clients:
                for client in self.clients:#Looking if the id is used
                    if client.id == mymsg.fID:
                        self.loginERR(False)
                        return
            self.clients.append(newclient)
            self.loginACK()
        elif mymsg.mType == MESSAGE.NEWGAME:
            if (mymsg.payload > 5) or (mymsg.payload < 3):
                self.newGameACK(True)
                return
            for client in self.clients:
                if (client.id == mymsg.fID) and (client.asock is mymsg.sock): #Probably, it is our client, but I want also check the psock
                    client.newgame(mymsg.payload)
                    self.newGameACK(False)
                    return
            raise ClientErr('Cannot Play: Client with id %i is not loged yet' % mymsg.fID)
        elif mymsg.mType == MESSAGE.GUESS:
            for client in self.clients:
                if (client.id == mymsg.fID) and (client.asock is mymsg.sock): #Probably, it is our client, but I want also check the psock
                    self.guessACK(client.guessgame(mymsg.payload), mymsg.payload, len(str(mymsg.payload)))
                    return
            raise ClientErr('Cannot Guess: Client with id %i is not loged yet' % mymsg.fID)
        elif mymsg.mType == MESSAGE.QUIT:
            for client in self.clients:
                if (client.id == mymsg.fID) and (client.asock is mymsg.sock): #Probably, it is our client, but I want also check the psock
                    self.quitACK()
                    print('Client with id %i has left the game' % mymsg.fID)
                    return
            raise ClientErr('Cannot quit: Client with id %i is not loged yet' % mymsg.fID)
        else:
            raise ClientErr('No valid request from client %i' % mymsg.fID)

    def loginACK(self):
        self.message._send_buffer = struct.pack('!IHIIH', self.message.mID, MESSAGE.LOGINACK, 0, self.message.fID,
                                                MESSAGE.ID_OK)

    def loginERR(self, out):
        if out:
            self.message._send_buffer = struct.pack('!IHIIH', self.message.mID, MESSAGE.LOGINACK, 0, self.message.fID,
                                                    MESSAGE.ID_OUTOFRANGE)
        else:
            self.message._send_buffer = struct.pack('!IHIIH', self.message.mID, MESSAGE.LOGINACK, 0, self.message.fID,
                                                    MESSAGE.ID_USED)

    def newGameACK(self, out):
        if out:
            self.message._send_buffer = struct.pack('!IHIIH', self.message.mID, MESSAGE.NEWGAMEACK, 0, self.message.fID,
                                                    MESSAGE.LENGTHOUTOFRANGE)
        else:
            self.message._send_buffer = struct.pack('!IHIIH', self.message.mID, MESSAGE.NEWGAMEACK, 0, self.message.fID,
                                                    MESSAGE.GAME_OK)

    def guessACK(self, BnC, guess, size):
        print('Tried: %i and gotten %i bulls and %i cows' % (guess, BnC[0], BnC[1]))
        if BnC == [size, 0]:#win
            self.message._send_buffer = struct.pack('!IHIIIIIB', self.message.mID, MESSAGE.GUESSACK, 0,
                                                    self.message.fID, guess, BnC[0], BnC[1], 1)
        else:
            self.message._send_buffer = struct.pack('!IHIIIIIB', self.message.mID, MESSAGE.GUESSACK, 0,
                                                    self.message.fID, guess, BnC[0], BnC[1], 0)

    def quitACK(self):
        self.message._send_buffer = struct.pack('!IHIIH', self.message.mID, MESSAGE.QUITACK, 0, self.message.fID,
                                                MESSAGE.QUIT_OK)

    def serve(self):
        try:
            while True:
                events = self.sel.select(timeout=None)
                for key, mask in events:
                    if key.data is None:#The connection is from the psocket and has to be accepted
                        self.wrap_accept(key.fileobj)
                    else:#Already accepted connection, just copy the content
                        self.message = key.data
                        try:
                            self.message.process_events(mask)
                            #Now process the message
                            if mask & selectors.EVENT_READ:
                                self.process_msg()
                                self.message._set_selector_events_mask('w')
                        except Exception as msg:
                            print('Error: %s' % str(msg))
                            for client in self.clients:# If there was a problem, close connection, and delete from clients
                                if client.asock is self.message.sock:
                                    self.clients.remove(client)
                                    break
                            self.message.close()
                            #raise
        except:#Unspected exception
            #print('Error: %s' % traceback.format_exc())
            raise
        finally:
            self.sel.close()


if __name__ == '__main__':
    newServer = Server(8888)
    newServer.serve()
