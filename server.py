from socket import *
from threading import Thread
import time
import struct
import math

# Const
SERVER_IP = '10.5.0.2'
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
    total_segments = math.ceil(file_size / BUFFER_SIZE)
    current_segment_count = 0
    bytes_sent = 0

    while bytes_sent < file_size:
        # create a payload message
        payload_data = MAGIC_COOKIE + struct.pack('B', PAYLOAD_TYPE) + struct.pack('!QQ', total_segments,
                                                                                   current_segment_count)

        payload_data += b"A" * min((file_size - bytes_sent), BUFFER_SIZE - 21)  # actual data
        udp_socket.sendto(payload_data, client_address)
        current_segment_count += 1
        bytes_sent += len(payload_data) - 21  # minus cookie and the header


def handle_tcp_connection(connection_socket, file_size):
    total_segments = math.ceil(file_size / BUFFER_SIZE)
    current_segment_count = 0
    bytes_sent = 0

    try:
        while bytes_sent < file_size:
            payload_data = (
                MAGIC_COOKIE +
                struct.pack('B', PAYLOAD_TYPE) +
                struct.pack('!QQ', total_segments, current_segment_count)
            )
            payload_data += b"A" * min((file_size - bytes_sent), BUFFER_SIZE - 21)  # Actual data
            connection_socket.send(payload_data)
            current_segment_count += 1
            print(current_segment_count)
            bytes_sent += len(payload_data) - 21  # Exclude header size

    except Exception as e:
        print(f"Error during TCP data transfer: {e}")
    finally:
        connection_socket.close()
        print("TCP connection closed.")


def start_server():
    Thread(target=broadcast_offer, daemon=True).start()
    print(f"Server started, listening on IP address {SERVER_IP}")
    # server starts listen for UDP connections

    def udp_server_start():
        # Create and bind UDP socket once
        udp_socket = socket(AF_INET, SOCK_DGRAM)
        udp_socket.bind(('', UDP_PORT))

        while True:
            data, addr = udp_socket.recvfrom(BUFFER_SIZE)
            if data.startswith(MAGIC_COOKIE) and data[4] == REQUEST_TYPE:
                print(f"connection established from user with ip :{addr}")
                file_size = struct.unpack('!Q', data[5:13])[0]
                Thread(target=handle_udp_connection, args=(udp_socket, addr, file_size), daemon=True).start()

    def tcp_server_start():
        # start the tcp and listen for connections.
        tcp_socket = socket(AF_INET, SOCK_STREAM)
        tcp_socket.setsockopt(SOL_SOCKET, SO_REUSEADDR, 1)
        tcp_socket.bind(('', TCP_PORT))
        tcp_socket.listen(5)

        # start server listening:
        while True:
            try:
                connection_socket, addr = tcp_socket.accept()
                print(f"TCP connection established from {addr}")
                data = connection_socket.recv(BUFFER_SIZE)
                if data.startswith(MAGIC_COOKIE) and data[4] == REQUEST_TYPE:
                    file_size = struct.unpack('!Q', data[5:13])[0]
                    Thread(target=handle_tcp_connection, args=(connection_socket, file_size), daemon=True).start()
                else:
                    print(f"Invalid request from {addr}")
                    connection_socket.close()
            except Exception as e:
                print(f"Error in TCP server: {e}")
                break


if __name__ == '__main__':
    try:
        start_server()
    except Exception as e:
        print(f"An error occurred in the main server: {e}")
