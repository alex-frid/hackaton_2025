from socket import *
from threading import Thread
import time
import struct
import math
import selectors
import ipaddress

# Const
SERVER_IP = gethostbyname(gethostname())
BUFFER_SIZE = 1024
BROADCAST_INTERVAL = 1
OFFER_TYPE = 0x02  # offer message type
REQUEST_TYPE = 0x03  # request message type
PAYLOAD_TYPE = 0x04  # Payload message type
MAGIC_COOKIE = b'\xAB\xCD\xDC\xBA'

# ANSI color codes
class Colors:
    HEADER = '\033[95m'
    OKBLUE = '\033[94m'
    OKCYAN = '\033[96m'
    OKGREEN = '\033[92m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'


def broadcast_offer(udp_port, tcp_port):
    # set up UDP socket for broadcast
    udp_socket = socket(AF_INET, SOCK_DGRAM)
    udp_socket.setsockopt(SOL_SOCKET, SO_BROADCAST, 1)
    data = MAGIC_COOKIE + struct.pack('B', OFFER_TYPE) + struct.pack('!HH', udp_port, tcp_port)

    while True:
        try:
            udp_socket.sendto(data, ('255.255.255.255', 9876))
            time.sleep(BROADCAST_INTERVAL)
        except Exception as e:
            print(Colors.FAIL + f"Error in broadcast_offer: {e}" + Colors.ENDC)
            break


def handle_udp_connection(client_address, file_size):
    """ Handle UDP connection and perform the data transfer operations"""
    try:
        udp_socket = socket(AF_INET, SOCK_DGRAM)
        total_segments = math.ceil(file_size / BUFFER_SIZE)
        current_segment_count = 0
        bytes_sent = 0

        while bytes_sent < file_size:
            # create a payload message
            payload_data = (
                    MAGIC_COOKIE +
                    struct.pack('B', PAYLOAD_TYPE) +
                    struct.pack('!QQ', total_segments, current_segment_count)
            )
            payload_data += b"A" * min((file_size - bytes_sent), BUFFER_SIZE - 21)  # actual data
            udp_socket.sendto(payload_data, client_address)
            current_segment_count += 1
            bytes_sent += len(payload_data) - 21  # minus cookie and the header
        print(Colors.OKGREEN + f"UDP transfer to {client_address} completed." + Colors.ENDC)
    except Exception as e:
        print(Colors.FAIL + f"Error in handle_udp_connection: {e}" + Colors.ENDC)


def handle_tcp_connection(connection_socket, file_size):
    try:
        payload_data = b"A" * file_size  # Actual data
        connection_socket.send(payload_data)
        print(Colors.OKGREEN + "TCP transfer completed." + Colors.ENDC)
    except Exception as e:
        print(Colors.FAIL + f"Error in handle_tcp_connection: {e}" + Colors.ENDC)
    finally:
        connection_socket.close()


def udp_server(sock):
    while True:
        try:
            data, addr = sock.recvfrom(BUFFER_SIZE)
            if data.startswith(MAGIC_COOKIE) and data[4] == REQUEST_TYPE:
                print(Colors.OKBLUE + f"Connection established from user with IP: {addr}" + Colors.ENDC)
                file_size = struct.unpack('!Q', data[5:13])[0]
                Thread(target=handle_udp_connection, args=(addr, file_size), daemon=True).start()
        except Exception as e:
            print(Colors.FAIL + f"Error in udp_server: {e}" + Colors.ENDC)


def tcp_server(sock):
    while True:
        try:
            connection_socket, addr = sock.accept()
            print(Colors.OKBLUE + f"TCP connection established from {addr}" + Colors.ENDC)
            data = connection_socket.recv(BUFFER_SIZE).decode()
            Thread(target=handle_tcp_connection, args=(connection_socket, int(data)), daemon=True).start()
        except Exception as e:
            print(Colors.FAIL + f"Error in tcp_server: {e}" + Colors.ENDC)


def start_server():
    # server starts listen for UDP connections
    udp_socket = socket(AF_INET, SOCK_DGRAM)
    udp_socket.bind(('', 0))
    udp_port = udp_socket.getsockname()[1]

    # start the tcp and listen for connections.
    tcp_socket = socket(AF_INET, SOCK_STREAM)
    tcp_socket.setsockopt(SOL_SOCKET, SO_REUSEADDR, 1)
    tcp_socket.bind(('', 0))
    tcp_port = tcp_socket.getsockname()[1]
    tcp_socket.listen()

    Thread(target=broadcast_offer, args=(udp_port, tcp_port), daemon=True).start()
    print(Colors.OKGREEN + f"Server started, listening on IP address {SERVER_IP}" + Colors.ENDC)

    tcp_server(tcp_socket)
    udp_server(udp_socket)

    # Keep the main thread alive
    while True:
        time.sleep(1)


if __name__ == '__main__':
    try:
        start_server()
    except Exception as e:
        print(Colors.FAIL + f"An error occurred in the main server: {e}" + Colors.ENDC)
