from socket import *
from threading import Thread
import time
import struct
import math
import selectors

# Const
SERVER_IP = gethostbyname(gethostname())
UDP_PORT = 8888
TCP_PORT = 8080
BUFFER_SIZE = 1024
BROADCAST_INTERVAL = 1
OFFER_TYPE = 0x02  # offer message type
REQUEST_TYPE = 0x03  # request message type
PAYLOAD_TYPE = 0x04  # Payload message type
MAGIC_COOKIE = b'\xAB\xCD\xDC\xBA'

# Selector for managing multiple sockets
sel = selectors.DefaultSelector()


def broadcast_offer():
    # set up UDP socket for broadcast
    udp_socket = socket(AF_INET, SOCK_DGRAM)
    udp_socket.setsockopt(SOL_SOCKET, SO_BROADCAST, 1)
    data = MAGIC_COOKIE + struct.pack('B', OFFER_TYPE) + struct.pack('!HH', UDP_PORT, TCP_PORT)

    while True:
        try:
            udp_socket.sendto(data, ('255.255.255.255', 1234))
            time.sleep(BROADCAST_INTERVAL)
        except Exception as e:
            print(f"Error in broadcast_offer: {e}")
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
        print(f"UDP transfer to {client_address} completed.")
    except Exception as e:
        print(f"Error in handle_udp_connection: {e}")


def handle_tcp_connection(connection_socket, file_size):
    try:
        payload_data = b"A" * file_size  # Actual data
        connection_socket.send(payload_data)
        print(f"TCP transfer completed.")
    except Exception as e:
        print(f"Error in handle_tcp_connection: {e}")
    finally:
        connection_socket.close()


def udp_server(sock):
    while True:
        try:
            data, addr = sock.recvfrom(BUFFER_SIZE)
            if data.startswith(MAGIC_COOKIE) and data[4] == REQUEST_TYPE:
                print(f"connection established from user with ip :{addr}")
                file_size = struct.unpack('!Q', data[5:13])[0]
                Thread(target=handle_udp_connection, args=(addr, file_size), daemon=True).start()
        except Exception as e:
            print(f"Error in udp_server: {e}")


def tcp_server(sock):
    while True:
        try:
            connection_socket, addr = sock.accept()
            print(f"TCP connection established from {addr}")
            data = connection_socket.recv(BUFFER_SIZE).decode()
            Thread(target=handle_tcp_connection, args=(connection_socket, int(data)), daemon=True).start()
        except Exception as e:
            print(f"Error in tcp_server: {e}")


def start_server():
    Thread(target=broadcast_offer, daemon=True).start()
    print(f"Server started, listening on IP address {SERVER_IP}")

    # server starts listen for UDP connections
    udp_socket = socket(AF_INET, SOCK_DGRAM)
    udp_socket.bind(('', UDP_PORT))
    sel.register(udp_socket, selectors.EVENT_READ, lambda: udp_server(udp_socket))

    # start the tcp and listen for connections.
    tcp_socket = socket(AF_INET, SOCK_STREAM)
    tcp_socket.setsockopt(SOL_SOCKET, SO_REUSEADDR, 1)
    tcp_socket.bind(('', TCP_PORT))
    tcp_socket.listen(5)
    sel.register(tcp_socket, selectors.EVENT_READ, lambda: tcp_server(tcp_socket))

    while True:
        events = sel.select()
        for key, _ in events:
            callback = key.data
            callback()


if __name__ == '__main__':
    try:
        start_server()
    except Exception as e:
        print(f"An error occurred in the main server: {e}")
