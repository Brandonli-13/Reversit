#!/usr/bin/env python3

from subprocess import Popen, PIPE, STDOUT
from shlex import split
from os import getcwd, chdir, system
from os.path import basename
from sys import exit
from socket import socket, AF_INET, SOCK_STREAM, SOL_SOCKET, SO_REUSEADDR
from argparse import ArgumentParser, ArgumentDefaultsHelpFormatter


def main():
    parser = ArgumentParser(description='reversit', formatter_class=ArgumentDefaultsHelpFormatter)

    parser.add_argument('-a', '--address', type=str, help='Set IP address to connect to (client) / IP address to listen for a connection on (server)')
    parser.add_argument('-p', '--port', type=int, help='Set port number to connect to (client) / port number to listen for a connection on (server)')
    parser.add_argument('-b', '--buffer', type=int, const=131072, nargs='?', default=131072, help='Set buffer size')
    parser.add_argument('-s', '--separator', type=str, const='<separator>', nargs='?', default='<separator>', help='Set separator between type of request and data, default: <separator>')
    parser.add_argument('-l', '--listen', action='store_true', help='Listen for incoming connections')

    args = parser.parse_args()

    match args.listen:
        case True:
            server = Server(args.address, args.port, args.buffer, args.separator)
            server.start()

        case False:
            client = Client(args.address, args.port, args.buffer, args.separator)
            try:
                client.connect()
            except KeyboardInterrupt:
                pass


class Server:
    def __init__(self, server_host: str, server_port: int, buffer_size: int, separator: str):
        self.server = socket(AF_INET, SOCK_STREAM)
        self.server.setsockopt(SOL_SOCKET, SO_REUSEADDR, 1)

        self.server_host = server_host
        self.server_port = server_port

        self.conn = None
        self.addr = None

        self.buffer_size = buffer_size

        self.separator = separator

        self.cwd = None

        self.received = None
        self.type = None

        self.data = None
        self.file = None
        self.filename = None

        self.command = None
        self.stdout = None

        self.end = None

    # start the server by binding to address and accept all incoming connections
    def start(self):
        self.server.bind((self.server_host, self.server_port))
        self.server.listen(5)
        self.conn, self.addr = self.server.accept()

        self.cwd = getcwd()

        self.conn.send(self.cwd.encode())

        try:
            self.receive()
        except KeyboardInterrupt:
            print('exit!!!')
            self.stdout = 'Server process was terminated. '
            self.end = 'terminated'
            self.send_error()
            exit()
        except Exception as e:
            self.stdout = 'A server-side error occurred: {0}'.format(e)
            self.end = 'error'
            self.send_error()
            exit()

    def restart(self):
        self.conn, self.addr = self.server.accept()

        self.cwd = getcwd()

        self.conn.send(self.cwd.encode())

        self.receive()

    def receive(self):
        while True:
            self.received = self.conn.recv(self.buffer_size).decode()
            self.type, self.data = tuple(self.received.split(self.separator))

            if self.type == 'command':
                self.command = split(self.data)

                self.receive_command()
            elif self.type[:9] == 'filename:':
                self.file = self.data

                self.receive_file()
            elif self.type == 'disconnect':
                self.conn.close()

                self.restart()

    # receive commands from client
    def receive_command(self):
        if self.command[0] == 'cd' and len(self.command) == 2:
            chdir(self.command[1])
            self.cwd = getcwd()
            self.stdout = 'Current Directory: {0}\n'.format(self.cwd)

        else:
            try:
                self.execute()
            except FileNotFoundError:
                self.stdout = 'Command not found: {0}\n'.format(self.command[0])

        self.send_command_output()

    def receive_file(self):
        self.filename = basename(self.type[9:])

        with open(self.filename, 'w') as file_handle:
            file_handle.write(self.file)
            file_handle.close()

    def execute(self):
        process = Popen(self.command, stdout=PIPE, stderr=STDOUT)

        stdout, stderr = process.communicate()
        self.stdout = stdout.decode()

    def send_command_output(self):
        self.conn.send((self.stdout + self.separator + self.cwd).encode())

    def send_error(self):
        self.conn.send((self.stdout + self.separator + self.end).encode())


class Client:
    def __init__(self, server_host: str, server_port: int, buffer_size: int, separator: str):
        from colorama import init

        init()

        self.client = socket(AF_INET, SOCK_STREAM)

        self.server_host = server_host
        self.server_port = server_port

        self.buffer_size = buffer_size

        self.separator = separator

        self.cwd = None

        self.received = None

        self.file = None
        self.filename = None

        self.command = None
        self.stdout = None

        self.end = None

    def connect(self):
        from colorama import Fore

        try:
            self.client.connect((self.server_host, self.server_port))
        except ConnectionRefusedError:
            print(Fore.RED + '\nError: Connection to server {0}:{1} refused.'.format(self.server_host,
                                                                                     self.server_port)
                  + Fore.RESET)
            exit()

        self.cwd = self.client.recv(self.buffer_size).decode()

        try:
            self.send()
        except KeyboardInterrupt:
            self.send_disconnect()

    def send(self):
        from colorama import Fore

        system('clear')
        print(Fore.GREEN + '\nConnected to {0}:{1}\n'.format(self.server_host, self.server_port) + Fore.RESET)

        while True:
            self.command = split(input(Fore.BLUE + self.cwd + Fore.RED + ' > ' + Fore.CYAN))

            match self.command[0]:
                case 'exit':
                    self.send_disconnect()
                case 'upload':
                    self.filename = self.command[1]

                    self.send_file()
                case _:
                    self.send_command()

    def send_command(self):
        self.client.send(('command' + self.separator + ' '.join(self.command)).encode())

        self.receive_command_output()

    def send_file(self):
        with open(self.filename, 'r') as file_handle:
            self.file = file_handle.read()
            file_handle.close()

        self.client.send(('filename:' + self.filename + self.separator + self.file).encode())
        print()

    def send_disconnect(self):
        self.client.send(('disconnect' + self.separator + 'disconnect').encode())

        exit()

    def receive_command_output(self):
        from colorama import Fore

        self.received = self.client.recv(self.buffer_size).decode()

        self.stdout, self.end = self.received.split(self.separator)

        if self.end in ['terminated', 'error']:
            print('\n' + Fore.RED + self.stdout)
            exit()
        else:
            self.cwd = self.end
            print('\n' + Fore.GREEN + self.stdout)


if __name__ == '__main__':
    main()
