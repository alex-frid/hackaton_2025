from socket import *
from threading import Thread
import time
import struct


# Const
SERVER_IP = '192.168.192.227'
UDP_PORT = 27069
TCP_PORT = 27069
BUFFER_SIZE = 1024
BROADCAST_INTERVAL = 1
OFFER_TYPE = 0x02  # offer message type
REQUEST_TYPE = 0x03  # request message type
PAYLOAD_TYPE = 0x04  # Payload message type
MAGIC_COOKIE = b'\xAB\xCD\xDC\xBA'


def broadcast_offer():
    # set up UDP socket for broadcast
    udp_socket = socket(AF_INET, SOCK_DGRAM)
    udp_socket.bind(('', UDP_PORT))


    while True:
        # Broadcast offer every second
        udp_socket.sendto(MAGIC_COOKIE + struct.pack('B', OFFER_TYPE) + struct.pack('!HH', UDP_PORT, TCP_PORT),
                          ("<broadcast>", UDP_PORT))
        time.sleep(BROADCAST_INTERVAL)


def handle_udp_connection(udp_socket, client_address,file_size):
    total_segments = file_size // BUFFER_SIZE
    segment_count = 0
    bytes_sent = 0
    start_time = time.time()

    while bytes_sent < file_size:
        # create a payload message
        current_segment_count = segment_count + 1
        payload_data = MAGIC_COOKIE + struct.pack('B', PAYLOAD_TYPE) + struct.pack('!QQ',total_segments, current_segment_count)
        payload_data += b"A" * min(file_size - bytes_sent, BUFFER_SIZE) # actual data

        udp_socket.sendto(payload_data, client_address)
        bytes_sent += len(payload_data) - 12  # minus cookie and the header
        segment_count += 1
        total_time = time.time() - start_time
        print(total_time)


def handle_tcp_connection():
    pass


def start_server():
    #Thread(target=broadcast_offer, daemon=True).start()
    broadcast_offer()
    # server starts listen for UDP connections

    # handle UDP connection
    while True:
        udp_socket = socket(AF_INET, SOCK_DGRAM)
        udp_socket.bind(('', UDP_PORT))
        data, addr = udp_socket.recvfrom(BUFFER_SIZE)
        if data.startswith(MAGIC_COOKIE) and data[4] == REQUEST_TYPE:
            file_size = struct.unpack('!Q', data[5:13])[0]
            Thread(target=handle_udp_connection, args=(udp_socket, addr, file_size),daemon=True).start()


if __name__ == '__main__':
    start_server()
