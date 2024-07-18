import socket
from sys import argv


class Server:
    """
        Class to represent a Server
    """

    def __init__(self) -> None:
        """
              initial method,
        """

        print('------------- Connector Server -------------\n')

        self.DPORT = 0

        # Get the server port if entered in argv !
        if len(argv) == 2:
            self.SERVER_PORT = int(argv[1])

        else:
            self.SERVER_PORT = 44444

    def run_server(self) -> None:
        """
            The method to run the server and wait for clients to connect to each other !
        """

        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        sock.bind(('0.0.0.0', self.SERVER_PORT))

        print(f'* Server Information> {Server.get_ip()}:{self.SERVER_PORT}')

        # a dictionary to save clients and connect them with ports
        clients = {}

        # a list to keep connected ips and ports
        connected = []

        while True:
            data, address = sock.recvfrom(1024)

            # send a 'ready' status to a peer if data is a 'connector'
            if data.decode('utf-8') == '0':
                print('+ Connection accepted from > {}'.format(address))
                sock.sendto(b'ready', address)
                continue

            # get the destination port if the data is not a 'connector'
            else:
                DPORT = int(data.decode('utf-8'))
                if (address[1], DPORT) not in clients: clients[(address[1], DPORT)] = []
                if address not in clients[(address[1], DPORT)]: clients[(address[1], DPORT)].append(address)

            # check if two clients are ready and connect them to each other
            results = [[i, clients[i]] for i in clients if len(clients[i]) > 1 and clients[i] not in connected]
            if len(results) > 0:
                connected.append(results[0][1])
                print("+ Connected > ", connected)

                sock.sendto('{} {} {}'.format(results[0][1][0][0], results[0][1][0][1], results[0][0][1]).encode(),
                            results[0][1][1])
                sock.sendto('{} {} {}'.format(results[0][1][1][0], results[0][1][1][1], results[0][0][1]).encode(),
                            results[0][1][0])
                continue

            # connect a disconnected peer to its friend peer !
            for i in clients:
                if len(clients[i]) > 1 and address in clients[i]:
                    index = clients[i].index(address)
                    reversed_index = 0 if index else 1

                    if not Server.check_online(clients[i][reversed_index][0], clients[i][reversed_index][1]):
                        clients[i] = [clients[i][index]]
                        continue

                    # send a disconnected peer the friend peer's information
                    sock.sendto('{} {} {}'.format(clients[i][reversed_index][0], i[0], i[1]).encode(),
                                clients[i][index])

                    print(f"+ Reconnecting {clients[i][index]} - {clients[i][reversed_index]} ...")

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


# Driver Code
if __name__ == '__main__':
    try:
        S = Server()
        S.run_server()

    finally:
        print("\n\n------------- Exiting P2P Messaging App -------------\n\n\n")
