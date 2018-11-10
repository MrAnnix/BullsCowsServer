#!/usr/bin/env python

import socket, select, sys, struct

#Constants
LOGIN = 0x01
LOGINACK = 0x11
ID_OK = 0x00
ID_USED = 0x11
ID_OUTOFRANGE = 0x12
ERROR = 0x13

NEWGAME = 0x02
NEWGAMEACK = 0x12

GUESS = 0x03
GUESSACK = 0x13

QUIT = 0x04
QUITACK = 0x14
QUIT_OK = 0x00

class Communications():
    def send(channel, *args):
        buf = marshall(args)
        value = socket.htonl(len(buf))
        size = struct.pack("L", value)
        channel.send(size)
        channel.send(buf)

    def receive(channel):
        size = struct.calcsize("L")
        size = channel.recv(size)
        try:
            size = socket.ntohl(struct.unpack("L", size)[0])
        except:
            return ''

        buf = ""

        while len(buf) < size:
            buf = channel.recv(size - len(buf))

        return unmarshall(buf)[0]

    def login(self, client):
        info = self.clientinfo[client]
        host, id = info[0][0], info[1]
        return '@'.join((id, host))

    def loginack(self, client):
        r=3

    def newgame(self, client):
        r=3

    def newgameack(self, client):
        r=3

    def guess(self, client):
        r=3

    def guessack(self, client):
        r=3

    def quit(self, client):
        r=3

    def quitack(self, client):
        r=3