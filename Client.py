import sys
import socket
import threading
from sys import argv
from os import listdir
from pickle import dump, load
from datetime import datetime

messages = []  # save messages when peer is offline !


class Client:
    """
        Class to represent a Client
    """

    ME = "[ME] > "  # Description text
    PEER_ONLINE = True  # Check if peer is online or not

    def __init__(self) -> None:
        """
              initial method,
        """

        print(f'------------- P2P Messaging App (ME:@{Client.get_ip()}) -------------\n')

        # Get the source port and destination port if entered in argv !
        if len(argv) == 3:
            self.SPORT = int(argv[1])
            self.DPORT = int(argv[2])

        else:
            self.SPORT = 60001
            self.DPORT = 60002

        # Connect to the server
        server = self.server_connect()

        # Wait for peer to get online
        ip, sport, dport = self.wait_for_peer(server)

        # Connect to peer
        self.connect_to_peer(ip, sport, dport)

        # Exchange data between peers
        self.exchanging_data_peer(ip, sport, dport)

    @staticmethod
    def get_ip() -> str:
        """
            The method to get the public ip address,

            Return:
                The string value of public ip address
        """

        socket_ = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        socket_.settimeout(0)

        try:
            socket_.connect(('10.254.254.254', 1))
            IP = socket_.getsockname()[0]

        except Exception:
            IP = '127.0.0.1'

        finally:
            socket_.close()

        return IP

    def server_connect(self) -> str:
        """
            The method to get ready to connect to server

            Return:
                The string value of server information
        """

        get_input = input("Enter Server [IP:PORT] > ").replace(" ", "")
        server_address = get_input.split(":")
        self.server = (server_address[0], int(server_address[1]))
        print('\n+ Connecting to the server ...')
        return f"{get_input}"

    def wait_for_peer(self, server: str) -> list:
        """
            The method to create a socket and wait for server to send 'ready',
            then get the peer's information !

            Parameters:
                server (str): The string value of server {address:port}.

            Return:
                The list of peer information !
        """

        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        sock.bind(('0.0.0.0', self.SPORT))
        sock.sendto(b'0', self.server)
        sock.sendto(str(self.DPORT).encode("utf-8"), self.server)

        while True:
            try:
                data = sock.recv(1024).decode()

            except ConnectionResetError:
                print(f'\n+ No connection to Server ! Exiting ...')
                sys.exit()

            if data.strip() == 'ready':
                print(f'+ Connected To {server}')
                print('+ Waiting for a peer ...')
                break

        data = sock.recv(1024).decode()
        # print('data:', data)
        ip, sport, dport = data.split(' ')
        sport = int(sport)
        dport = int(dport)

        print('\n------------- Connected -------------\n')
        print(f'IP: {ip}, Source: {sport}, Destination: {dport}')

        self.ME = "[" + "ME".center(len(ip)) + f"] > "

        return [ip, sport, dport]

    def connect_to_peer(self, ip: str, sport: int, dport: int) -> None:
        """
            The method to create a socket and connect to peer !

            Parameters:
                ip (str): The string value of peer IP.
                sport (int): The integer value of peer source port.
                dport (int): The integer value of peer destination port.
        """

        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        sock.bind(('0.0.0.0', sport))
        sock.sendto(b'0', (ip, dport))

    def exchanging_data_peer(self, ip, sport, dport) -> None:
        """
            The method to create a socket, listener and a chat section !

            Parameters:
                ip (str): The string value of peer IP.
                sport (int): The integer value of peer source port.
                dport (int): The integer value of peer destination port.
        """
        global messages

        print('\n------------- Chat Section -------------\n')

        # create a new thread for listener
        listener = threading.Thread(target=self.listen, daemon=True, args=(ip, sport,))

        # open a socket for sending online status
        alive_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        alive_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        alive_socket.setsockopt(socket.SOL_SOCKET, socket.SO_KEEPALIVE, 1)
        alive_socket.bind(('0.0.0.0', sport))
        alive_socket.listen()
        sendOnline = threading.Thread(target=Client.send_online, daemon=True, args=(alive_socket,))

        # start threads
        listener.start()
        sendOnline.start()

        # open a socket for sending messages
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        sock.bind(('0.0.0.0', dport))

        while True:
            msg = input(f'{"*" if self.PEER_ONLINE else " "}[{datetime.now().strftime("%X")}] {self.ME}')

            # check if peer is online or not
            is_online = Client.check_online(ip, sport)

            # save the messages in case that the peer is offline
            if not is_online:
                self.PEER_ONLINE = False
                messages.append(msg)

            else:
                if messages:
                    self.PEER_ONLINE = True

                    # Send all messages after peer get online again
                    for message in messages:
                        sock.sendto(message.encode(), (ip, sport))
                    messages = []

            sock.sendto(msg.encode(), (ip, sport))

    @staticmethod
    def check_online(ip, sport) -> bool:
        """
            The method to check if the peer is online or not using TCP Socket with 0.5s timeout !

            Parameters:
                ip (str): The string value of peer IP.
                sport (int): The integer value of peer source port.

            Return:
                The boolean value of peer's online status
        """

        try:
            alive_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            alive_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            alive_socket.settimeout(0.5)
            alive_socket.connect((ip, sport))
            alive_socket.close()

            return True

        except Exception as E:
            return False

    @staticmethod
    def send_online(alive_socket) -> None:
        """
            The method to accept TCP connection for keeping alive !

            Parameters:
                alive_socket : The TCP socket to be accepted !
        """

        while True:
            _, _ = alive_socket.accept()

    def listen(self, ip, sport) -> None:
        """
            The method to listen on the UDP socket to receive messages !

            Parameters:
                ip (str): The string value of peer IP.
                sport (int): The integer value of peer source port.
        """
        global messages

        # create a UDP socket
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        sock.bind(('0.0.0.0', sport))

        while True:
            # Get the data
            data = sock.recvfrom(1024)

            # Clear the line and print a new line with peer's message
            write = sys.stdout.write
            write('\b' * 100)
            write(
                f'{"*" if self.PEER_ONLINE else " "}[{datetime.now().strftime("%X")}] [{ip}] > {data[0].decode("utf-8")}\n{"*" if self.PEER_ONLINE else " "}[{datetime.now().strftime("%X")}] {self.ME}')

            if messages:
                self.PEER_ONLINE = True

                # Send all messages after peer get online again
                for message in messages + ["\n"]:
                    sock.sendto(message.encode(), (ip, sport))
                messages = []


# Driver Code
if __name__ == '__main__':
    try:
        if 'saved.msg' in listdir("."):
            # Getting back the saved messages !
            with open('saved.msg', 'rb') as f:
                messages = load(f)

            # empty the file
            with open('saved.msg', 'wb') as f:
                dump([], f)

        C = Client()

    finally:
        # Saving the messages !
        with open('saved.msg', 'wb') as f:
            dump(messages, f)

        print("\n\n------------- Exiting P2P Messaging App -------------\n\n\n")
