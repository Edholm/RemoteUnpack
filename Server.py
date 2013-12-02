#!/usr/bin/python
""" This is the server application that listens for connections and
unpacks archives in its own thread.

Copyright 2013 Emil Edholm <emil@edholm.it>

This program is free software: you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation, either version 3 of the License, or
(at your option) any later version.

This program is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU General Public License for more details.

You should have received a copy of the GNU General Public License
along with this program.  If not, see <http://www.gnu.org/licenses/>.

"""

#import socket
#import threading
import socketserver
import json
import os
import time

# The protocol this server supports/manages.
protocol = "RU/0.4"


def _recvall(sock, n):
    data = b''
    while len(data) < n:
        packet = sock.recv(n - len(data))
        if not packet:
            return None
        data += packet
    return data


def receive(sock):
    # receive length first.
    rawLength = _recvall(sock, 4)
    if not rawLength:
        return None
    from struct import unpack
    msgLen = unpack('!I', rawLength)[0]

    return _recvall(sock, msgLen).decode()


class ThreadedTCPRequestHandler(socketserver.BaseRequestHandler):

    def handle(self):
        addr, port = self.client_address
        import datetime
        print("Connection from {}:{} on {} {}".format(addr, port, datetime.datetime.now() , "{"))
        msgRaw = receive(self.request)
        msg = ''
        if msgRaw is not None:
            msg = json.loads(msgRaw)
        else:
            print("{}:{} closed the connection".format(addr, port))
            return False

        print("\tRequest: method {} over protocol {} from {}:{}".format(msg['method'], msg['protocol'], addr, port))

        if not self.verify_protocol(msg['protocol']):
            self.reply_with_code('506', 'Protocol Not Supported')
            print("}")
            return

        # Try calling the method requested
        try:
            func_name = "handle_" + msg['method'].lower()
            func = getattr(self, func_name)
            func(msg)
        except AttributeError:
            self.reply_with_code('501', 'Not Implemented')
        print("}")

    def verify_protocol(self, client_protocol):
        """Verify we're using the same protocol."""
        if not protocol == client_protocol:
            return False
        return True

    def handle_get(self, msg):
        """ The GET method is equivalent to the *nix command ls.

            The method will return the list in an arbitrarily order

        """
        if os.path.lexists(msg['path']):
            print("\tSending dir contents for " + msg['path'])
            dir_contents = (os.listdir(msg['path']))
            self.reply_with_code(data=dir_contents)
        else:
            self.reply_with_code(404, "Not Found")

    def handle_unpack(self, msg):
        # Set client ready for receiveing progress output
        self.reply_with_code('202', 'Accepted')
        time.sleep(1)
        i = 0
        while i <= 100:
            progress = "{}%".format(i)
            self.reply_with_code("206", "Partial Content", progress)
            time.sleep(0.1)
            i += 1
        time.sleep(1)
        self.reply_with_code()
        print("done")

    def reply_with_code(self, code='200', phrase='OK', data=''):
        addr, port = self.client_address
        print("\tReply: code {} - {} to {}:{}".format(code, phrase, addr, port))
        from struct import pack
        reply = json.dumps({
            'protocol': protocol,
            'code':     code,
            'phrase':   phrase,
            'data':     data}).encode()
        # Size of message then actual message
        msg = pack("!I", len(reply)) + reply
        self.request.sendall(msg)


class ThreadedTCPServer(socketserver.ThreadingMixIn, socketserver.TCPServer):
    def __init__(self, server_address, RequestHandlerClass):
        self.allow_reuse_address = True
        socketserver.TCPServer.__init__(self, server_address,
                                        RequestHandlerClass)


if __name__ == '__main__':
    HOST, PORT = "localhost", 1337
    server = ThreadedTCPServer((HOST, PORT), ThreadedTCPRequestHandler)
    try:
        print("Server listening on {}:{}".format(HOST, PORT))
        server.serve_forever()
    except KeyboardInterrupt:
        print("Shutting down server...")
        server.shutdown()
