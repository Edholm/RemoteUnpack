#!/usr/bin/python
# This is the server application that listens for connections and
# unpacks archives in its own thread. 
# 
# Copyright 2013 Emil Edholm <emil@edholm.it>
# 
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.

import socket
import threading
import socketserver
import json, os, time

# The protocol this server supports/manages.
protocol = "RU/0.3"

class ThreadedTCPRequestHandler(socketserver.BaseRequestHandler):

    def handle(self):
        addr, port = self.client_address
        print("Connection from {}:{}".format(addr, port))
        msg = json.loads(self.request.recv(1024).decode())
        
        print("Received: {}".format(msg))

        # Try calling the method requested 
        try:
            func_name = "handle_" + msg['method'].lower()
            func = getattr(self, func_name)
            func(msg)
        except AttributeError:
            self.reply_with_code('501', 'Not Implemented')

    def verify_protocol(self,client_protocol):
        """Verify we're using the same protocol."""
        if not protocol == client_protocol:
            self.reply_with_code('506', 'Protocol Not Supported')
            return False
        return True

    def handle_bepa(self, msg):
        self.reply_with_code()
        time.sleep(1)
        self.reply_with_code()
        self.reply_with_code()


    def handle_get(self, msg):
        """ The GET method is equivalent to the *nix command ls
            The method will return the list in an arbitrarily order"""
        if not self.verify_protocol(msg['protocol']):
            return
        
        if os.path.lexists(msg['path']):
             print("Replying with directory contents")
             dir_contents = "\n".join(os.listdir(msg['path']))
             self.reply_with_code(data = dir_contents)
        else:
             self.reply_with_code(404, "Not Found")

    def handle_unpack(self, msg):
        if not self.verify_protocol(msg['protocol']):
            return

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

    def reply_with_code(self, code = '200', phrase = 'OK', data = ""):
            reply = json.dumps({
                'protocol' : protocol, 
                'code'     : code, 
                'phrase'   : phrase,
                'data'     : data})
            self.request.sendall(reply.encode())

class ThreadedTCPServer(socketserver.ThreadingMixIn, socketserver.TCPServer):
    pass


if  __name__ =='__main__':
    HOST, PORT = "localhost", 1337 

    server = ThreadedTCPServer((HOST, PORT), ThreadedTCPRequestHandler)
    server.allow_reuse_address = True
    ip, port = server.server_address

    try:
        print("Server listening on {}:{}".format(HOST, PORT))
        server.serve_forever()
    except KeyboardInterrupt:
        print("Shutting down server...")
        server.shutdown()