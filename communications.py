#!/usr/bin/env python

#BASED ON this grat tutoril: https://realpython.com/python-sockets

import socket, selectors, sys, struct

#We have to avoid constant changes
def constant(f):
    def fset(self, value):
        raise TypeError
    def fget(self):
        return f()
    return property(fget, fset)

class _Message():
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
        0x12

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

MESSAGE = _Message()

class NoValidMessage(Exception):
    pass

class Message:
    def __init__(self, selector, sock, addr):
        self.selector = selector
        self.sock = sock
        self.addr = addr
        self._recv_buffer = b''
        self._send_buffer = b''
        self.mID = 0
        self.mType = 0
        self.fID = 0
        self.tID = 0
        self.payload = 0
        self.error = 0

    def _read(self):
        try:
            # Should be ready to read
            data = self.sock.recv(18)#No more data is needed max_size = 4B+2B+4B+4B+4B
        except BlockingIOError as e:
            print('Error: %s' % str(e[1]))
            # Resource temporarily unavailable (errno EWOULDBLOCK)
            pass
        else:
            if data:
                self._recv_buffer += data
            else:
                raise RuntimeError('Peer closed by ' + str(self.addr[0]) + ':' + str(self.addr[1]))

    def _write(self):
        if self._send_buffer:
            try:# Should be ready to write
                sent = self.sock.send(self._send_buffer)
            except BlockingIOError:# Resource temporarily unavailable (errno EWOULDBLOCK)
                pass
            else:
                self._send_buffer = self._send_buffer[sent:]
                # Close when the buffer is drained. The response has been sent.
                if sent and not self._send_buffer:
                    self.close()

    def process_events(self, mask):
        if mask & selectors.EVENT_READ:
            self.read()
        if mask & selectors.EVENT_WRITE:
            self.write()

    def read(self):
        self._read()
        if len(self._recv_buffer) == 14:
            mId, mType, mFrom, mTo = struct.unpack('!IHII', self._recv_buffer)
        elif len(self._recv_buffer) == 16:
            mId, mType, mFrom, mTo, mPayload = struct.unpack('!IHIIH', self._recv_buffer)
            self.payload = mPayload
        elif len(self._recv_buffer) == 18:
            mId, mType, mFrom, mTo, mPayload = struct.unpack('!IHIII', self._recv_buffer)
            self.payload = mPayload
        else:
            self.error = 0x13
            raise NoValidMessage('No valid message received from ' + str(self.addr[0]) + ':' + str(self.addr[1]))

        print('Size: %i' % len(self._recv_buffer))
        self.mID = mId
        self.mType = mType
        self.fID = mFrom
        self.tID = mTo

    def write(self):
        #If something to send

        self._write()

    def close(self):
        try:
            self.selector.unregister(self.sock)
        except:
            print('Error: %s' % sys.exc_info()[0])
        try:
            self.sock.close()
        except:
            print('Error: %s' % sys.exc_info()[0])
        finally:
            # Delete reference to socket object for garbage collection
            self.sock = None