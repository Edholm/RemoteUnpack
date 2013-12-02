#!/usr/bin/python
# This is a example CLI client that can be used to unpack archives
# and prints the status of the progress.
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
import json

HOST = "localhost"
PORT = 1337


def send(sock, message):
    from struct import pack
    msgRaw = pack("!I", len(message)) + message.encode()
    sock.sendall(msgRaw)


def recvall(sock, n):
    data = b''
    while len(data) < n:
        packet = sock.recv(n - len(data))
        if not packet:
            return None
        data += packet
    return data


def receive(sock):
    # receive length first.
    rawLength = recvall(sock, 4)
    if not rawLength:
        return None
    from struct import unpack
    msgLen = unpack('!I', rawLength)[0]

    return recvall(sock, msgLen).decode()


class Client(object):
    def __init__(self, sock=None):
        if sock is None:
            self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        else:
            self.sock = sock

    def connect(self, host, port):
        try:
            self.sock.connect((host, port))
            return True
        except ConnectionRefusedError:
            print("Server ({}:{}) refused connection".format(host, port))
            return False

    def disconnect(self):
        self.sock.shutdown(socket.SHUT_RDWR)
        self.sock.close()

if __name__ == '__main__':
    client = Client()
    success = client.connect(HOST, PORT)
    if success:
        msg = {'method':   'bepa',
               'path':     '/home/eda/',
               'protocol': 'RU/0.3'}
        send(client.sock, json.dumps(msg))

        msg = receive(client.sock)
        print(msg + "\n")
        msg = receive(client.sock)
        print(msg + "hej\n")
        msg = receive(client.sock)
        print(msg)
        #print(msg['code'])
        #if msg['code'] == '202':
        #    print("Ready to receive progress")
        #    msg = json.loads(client.receive())
        #    print(msg['code'])
        #    while msg['code'] == '206':
        #        print(msg['data'])
        #        msg = json.loads(client.receive())

        #print(msg['phrase'])
        client.disconnect()
