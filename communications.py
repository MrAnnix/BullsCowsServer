#!/usr/bin/env python

#  BASED ON this grat tutoril: https://realpython.com/python-sockets

import socket, selectors, sys, struct

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
        self.status = 0

    def _read(self):
        try:
            data = self.sock.recv(32)  # No more data is needed max_size = 4B+2B+4B+4B+4B = 18B so 2^5 = 32
        except BlockingIOError as e:  # Resource temporarily unavailable (errno EWOULDBLOCK)
            print('Error: %s' % str(e))
            pass
        else:
            if data:
                self._recv_buffer += data
            else:
                raise RuntimeError('Peer closed by ' + str(self.addr[0]) + ':' + str(self.addr[1]))

    def _write(self):
        if self._send_buffer:
            try:  # Should be ready to write
                sent = self.sock.send(self._send_buffer)
                self.set_selector_events_mask('r')
            except BlockingIOError as e:  # Resource temporarily unavailable (errno EWOULDBLOCK)
                print('Error: %s' % str(e))
                pass
            else:
                if sent:
                    self._send_buffer = self._send_buffer[sent:]
                else:
                    raise RuntimeError('Peer closed by ' + str(self.addr[0]) + ':' + str(self.addr[1]))

    def set_selector_events_mask(self, mode):
        """Set selector to listen for events: mode is 'r', 'w', or 'rw'."""
        if mode == "r":
            events = selectors.EVENT_READ
        elif mode == "w":
            events = selectors.EVENT_WRITE
        elif mode == "rw":
            events = selectors.EVENT_READ | selectors.EVENT_WRITE
        else:
            raise ValueError('Invalid events mask mode')
        self.selector.modify(self.sock, events, data=self)

    def process_events(self, mask):
        if mask & selectors.EVENT_READ:
            self.read()
            self._recv_buffer = b'' # Drain buffer
        if mask & selectors.EVENT_WRITE:
            self.write()
            self._send_buffer = b''

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

        self.mID = mId
        self.mType = mType
        self.fID = mFrom
        self.tID = mTo

    def write(self):
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
