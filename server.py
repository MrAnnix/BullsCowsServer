#!/usr/bin/env python

#  BASED ON this great tutorial: https://realpython.com/python-sockets

import socket, selectors, sys, signal, struct, communications, bullsandcows


def constant(f):  # We want to avoid accidental constant changes
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
    asock = None  # The active socket file descriptor is unique for every client
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
            print('Client with id %i has logged in' % ID)
        else:
            raise ClientErr('Cannot login: Client with ID %i, is already logged in' % id)


class Server():
    def __init__(self, port):
        self.sel = selectors.DefaultSelector()
        # Client info storage
        self.clients = []
        # The message actual message to be processed
        self.message = None
        # The pending events
        self.events = None
        # Passive socket creation
        self.p_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.p_sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        try:
            self.p_sock.bind(('0.0.0.0', port))
        except socket.error as msg:
            print('Error: %s' % str(msg))
            sys.exit()
        self.p_sock.listen()
        self.p_sock.setblocking(False)
        self.sel.register(self.p_sock, selectors.EVENT_READ, data=None)
        # Handling signals
        signal.signal(signal.SIGINT, self.signal_handler)

    def wrap_accept(self, sock):
        conn, addr = sock.accept()  # Should be ready to read
        conn.setblocking(False)
        self.message = communications.Message(self.sel, conn, addr)
        events = selectors.EVENT_READ  # First we have to read
        self.sel.register(conn, events, data=self.message)

    def signal_handler(self, signum, frame):  # Better than treat as a KeyboardInterrupt
        if signum == signal.SIGINT:
            try:
                # Close all existing client sockets
                self.sel.close()  # To be reviewed
                # Close the listening socket
                self.p_sock.close()
            except Exception as e:
                print(str(e))
            print('Closing server SIGINT received')
            #sys.exit(-1)

    def process_msg(self):
        mymsg = self.message
        if mymsg.mType == MESSAGE.LOGIN:
            if (mymsg.fID == 0) or (mymsg.fID > 200):
                self.login_err(True)
                return
            newclient = ClientInfo()
            newclient.login(mymsg.fID, mymsg.addr, mymsg.sock)
            if self.clients:
                for client in self.clients:  # Looking if the id is used
                    if client.id == mymsg.fID:
                        self.login_err(False)
                        return
            self.clients.append(newclient)
            self.login_ack()
        elif mymsg.mType == MESSAGE.NEWGAME:
            if (mymsg.payload > 5) or (mymsg.payload < 3):
                self.new_game_err(True)
                return
            for client in self.clients:
                # Probably, it is our client, but we want also check the p_sock to avoid spoofing
                if (client.id == mymsg.fID) and (client.asock is mymsg.sock):
                    client.newgame(mymsg.payload)
                    self.new_game_ack()
                    return
            self.new_game_err(False)
            self.message.write()  # Force error notification before exception and socket close
            raise ClientErr('Cannot Play: Client with id %i is not logged yet' % mymsg.fID)
        elif mymsg.mType == MESSAGE.GUESS:
            for client in self.clients:
                # Probably, it is our client, but we want also check the p_sock to avoid spoofing
                if (client.id == mymsg.fID) and (client.asock is mymsg.sock):
                    self.guess_ack(client.guessgame(mymsg.payload), mymsg.payload, client.length)
                    return
            self.guess_ack([0, 0], 0, 0)
            self.message.write()  # Force response before exception and socket close
            raise ClientErr('Cannot Guess: Client with id %i is not logged yet' % mymsg.fID)
        elif mymsg.mType == MESSAGE.QUIT:
            for client in self.clients:
                # Probably, it is our client, but we want also check the p_sock to avoid spoofing
                if (client.id == mymsg.fID) and (client.asock is mymsg.sock):
                    self.quit_ack()
                    return
            self.quit_err()
            self.message.write()  # Force error notification before exception and socket close
            raise ClientErr('Cannot quit: Client with id %i is not logged yet' % mymsg.fID)
        else:
            raise ClientErr('No valid request from client %i' % mymsg.fID)

    def login_ack(self):
        self.message._send_buffer = struct.pack('!IHIIH', self.message.mID, MESSAGE.LOGINACK, 0, self.message.fID,
                                                MESSAGE.ID_OK)

    def login_err(self, out):
        if out:
            self.message._send_buffer = struct.pack('!IHIIH', self.message.mID, MESSAGE.LOGINACK, 0, self.message.fID,
                                                    MESSAGE.ID_OUTOFRANGE)
        else:
            self.message._send_buffer = struct.pack('!IHIIH', self.message.mID, MESSAGE.LOGINACK, 0, self.message.fID,
                                                    MESSAGE.ID_USED)

    def new_game_ack(self):
        self.message._send_buffer = struct.pack('!IHIIH', self.message.mID, MESSAGE.NEWGAMEACK, 0, self.message.fID,
                                                MESSAGE.GAME_OK)

    def new_game_err(self, out):
        if out:
            self.message._send_buffer = struct.pack('!IHIIH', self.message.mID, MESSAGE.NEWGAMEACK, 0, self.message.fID,
                                                    MESSAGE.LENGTHOUTOFRANGE)
        else:
            self.message._send_buffer = struct.pack('!IHIIH', self.message.mID, MESSAGE.NEWGAMEACK, 0, self.message.fID,
                                                    MESSAGE.ERROR)

    def guess_ack(self, bnc, guess, size):
        print('Client %i has tried: %i and gotten %i bulls and %i cows' % (self.message.fID, guess, bnc[0], bnc[1]))
        if bnc == [size, 0]:  # Client has won
            self.message._send_buffer = struct.pack('!IHIIIIIB', self.message.mID, MESSAGE.GUESSACK, 0,
                                                    self.message.fID, guess, bnc[0], bnc[1], 1)
            print('Client %i wins' % self.message.fID)
        else:
            self.message._send_buffer = struct.pack('!IHIIIIIB', self.message.mID, MESSAGE.GUESSACK, 0,
                                                    self.message.fID, guess, bnc[0], bnc[1], 0)

    def quit_ack(self):
        print('Client with id %i has left the game' % self.message.fID)
        self.message._send_buffer = struct.pack('!IHIIH', self.message.mID, MESSAGE.QUITACK, 0, self.message.fID,
                                                MESSAGE.QUIT_OK)

    def quit_err(self):
        self.message._send_buffer = struct.pack('!IHIIH', self.message.mID, MESSAGE.QUITACK, 0, self.message.fID,
                                                MESSAGE.ERROR)

    def serve(self):
        try:
            while True:
                self.events = self.sel.select(timeout=None)
                for key, mask in self.events:
                    if key.data is None:  # The connection is from the passive socket and has to be accepted
                        self.wrap_accept(key.fileobj)
                    else:  # Already accepted connection, just copy the content
                        self.message = key.data
                        try:
                            self.message.process_events(mask)
                            # Now process the message
                            if mask & selectors.EVENT_READ:
                                self.process_msg()
                                self.message.set_selector_events_mask('w')
                        except Exception as msg:
                            print(str(msg))
                            # If there was a problem, close connection, and delete from clients
                            for client in self.clients:
                                if client.asock is self.message.sock:
                                    self.clients.remove(client)
                                    break
                            self.message.close()
        except:  # Not expected exception
            print('Error hey: %s' % sys.exc_info()[0])
        finally:
            self.sel.close()


if __name__ == '__main__':
    newServer = Server(8888)
    newServer.serve()
