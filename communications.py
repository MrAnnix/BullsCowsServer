#!/usr/bin/env python

import socket, selectors, sys, io, json, struct

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
        self.payload = b''
        self.error = 0x00

    def _set_selector_events_mask(self, mode):
        """Set selector to listen for events: mode is 'r', 'w', or 'rw'."""
        if mode == "r":
            events = selectors.EVENT_READ
        elif mode == "w":
            events = selectors.EVENT_WRITE
        elif mode == "rw":
            events = selectors.EVENT_READ | selectors.EVENT_WRITE
        else:
            raise ValueError(f"Invalid events mask mode {repr(mode)}.")
        self.selector.modify(self.sock, events, data=self)

    def _read(self):
        try:
            # Should be ready to read
            data = self.sock.recv(18)#No more data is needed max_size = 4B+2B+4B+4B+4B
        except BlockingIOError:
            # Resource temporarily unavailable (errno EWOULDBLOCK)
            pass
        else:
            if data:
                self._recv_buffer += data
            else:
                raise RuntimeError("Peer closed.")

    def _write(self):
        if self._send_buffer:
            print("sending", repr(self._send_buffer), "to", self.addr)
            try:
                # Should be ready to write
                sent = self.sock.send(self._send_buffer)
            except BlockingIOError:
                # Resource temporarily unavailable (errno EWOULDBLOCK)
                pass
            else:
                self._send_buffer = self._send_buffer[sent:]
                # Close when the buffer is drained. The response has been sent.
                if sent and not self._send_buffer:
                    self.close()

    def _create_message(self, *, content_bytes, content_type, content_encoding):
        jsonheader = {
            "byteorder": sys.byteorder,
            "content-type": content_type,
            "content-encoding": content_encoding,
            "content-length": len(content_bytes),
        }
        jsonheader_bytes = self._json_encode(jsonheader, "utf-8")
        message_hdr = struct.pack(">H", len(jsonheader_bytes))
        message = message_hdr + jsonheader_bytes + content_bytes
        return message

    def process_events(self, mask):
        if mask & selectors.EVENT_READ:
            self.read()
        if mask & selectors.EVENT_WRITE:
            self.write()

    def read(self):
        self._read()
        if len(self._recv_buffer) == 14:
            mId, mType, mFrom, mTo = struct.unpack('!ihii', self._recv_buffer)
        elif len(self._recv_buffer) == 16:
            mId, mType, mFrom, mTo, mPayload = struct.unpack('!ihiih', self._recv_buffer)
            self.payload = mPayload
        elif len(self._recv_buffer) == 18:
            mId, mType, mFrom, mTo, mPayload = struct.unpack('!ihiii', self._recv_buffer)
            self.payload = mPayload
        else:
            self.error = 0x13
            return

        self.mID = mId
        self.mType = mType
        self.fID = mFrom
        self.tID = mTo

    def write(self):
        if self.request:
            if not self.response_created:
                self.create_response()

        self._write()

    def close(self):
        try:
            self.selector.unregister(self.sock)

        try:
            self.sock.close()
        finally:
            # Delete reference to socket object for garbage collection
            self.sock = None

