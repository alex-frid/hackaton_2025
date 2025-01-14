from socket import *
from threading import Thread
import time
import struct

# Const
SERVER_IP = "10.0.0.3"
UDP_PORT = 8888
TCP_PORT = 8080
BUFFER_SIZE = 1024
BROADCAST_INTERVAL = 1
OFFER_TYPE = 0x02  # offer message type
REQUEST_TYPE = 0x03  # request message type
PAYLOAD_TYPE = 0x04  # Payload message type
MAGIC_COOKIE = b'\xAB\xCD\xDC\xBA'


def broadcast_offer():
    # set up UDP socket for broadcast
    udp_socket = socket(AF_INET, SOCK_DGRAM)
    udp_socket.setsockopt(SOL_SOCKET, SO_BROADCAST, 1)
    data = MAGIC_COOKIE + struct.pack('B', OFFER_TYPE) + struct.pack('!HH', UDP_PORT, TCP_PORT)

    while True:
        # Broadcast offer every second
        udp_socket.sendto(data, ('255.255.255.255', 1234))
        time.sleep(BROADCAST_INTERVAL)


def handle_udp_connection(udp_socket, client_address, file_size):
    """ Handle UDP connection and perform the data transfer operations"""
    total_segments = file_size // BUFFER_SIZE
    segment_count = 0
    bytes_sent = 0

    while bytes_sent < file_size:
        # create a payload message
        current_segment_count = segment_count + 1
        payload_data = MAGIC_COOKIE + struct.pack('B', PAYLOAD_TYPE) + struct.pack('!QQ', total_segments
                                                                                           ,current_segment_count)
        payload_data += b"A" * min(file_size - bytes_sent, BUFFER_SIZE)  # actual data

        udp_socket.sendto(payload_data, client_address)
        bytes_sent += len(payload_data) - 12  # minus cookie and the header
        segment_count += 1

def handle_tcp_connection():
    # TODO: write tcp
    pass

def start_server():
    Thread(target=broadcast_offer, daemon=True).start()
    print(f"Server started, listening on IP address {SERVER_IP}")
    # server starts listen for UDP connections

    # handle UDP connection
    while True:
        udp_socket = socket(AF_INET, SOCK_DGRAM)
        udp_socket.bind(('', UDP_PORT))
        data, addr = udp_socket.recvfrom(BUFFER_SIZE)
        if data.startswith(MAGIC_COOKIE) and data[4] == REQUEST_TYPE:
            print(f"connection established from user with ip :{addr}")
            file_size = struct.unpack('!Q', data[5:13])[0]
            Thread(target=handle_udp_connection, args=(udp_socket, addr, file_size), daemon=True).start()

    # handle TCP connection
    # TODO : create TCP connection


if __name__ == '__main__':
    start_server()
