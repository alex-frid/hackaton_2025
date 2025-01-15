from socket import *
from threading import Thread
import struct
import time

# Const
BUFFER_SIZE = 1024
MAGIC_COOKIE = b'\xAB\xCD\xDC\xBA'  # Magic cookie
REQUEST_TYPE = 0x03  # request message type
OFFER_TYPE = 0x02  # offer message type
PAYLOAD_TYPE = 0x04  # Payload message type


class Client:
    def __init__(self):
        self.file_size = 0
        self.server_ip = None
        self.UDP_PORT = None
        self.TCP_PORT = None
        self.num_tcp_connections = 1
        self.num_udp_connections = 1
        self.sock_udp = socket(AF_INET, SOCK_DGRAM)
        self.sock_tcp = socket(AF_INET, SOCK_STREAM)
        self.state = "Startup"

    def set_parameters(self):
        """ask user for parameters"""
        self.file_size = int(input("Enter the file size (in bytes): "))
        self.num_tcp_connections = int(input("Enter the number of TCP connections: "))
        self.num_udp_connections = int(input("Enter the number of UDP connections: "))
        self.state = "Looking for a server"

    def listen_for_offers(self):
        """listen for offer requests and select the first server found"""
        udp_socket = socket(AF_INET, SOCK_DGRAM)
        udp_socket.bind(('', 1234))
        print("Client started, listening for offer requests...")

        while True:
            data, addr = udp_socket.recvfrom(BUFFER_SIZE)
            if data.startswith(MAGIC_COOKIE) and struct.unpack('B', data[4:5])[0] == OFFER_TYPE:  # Offer message
                self.UDP_PORT, self.TCP_PORT = struct.unpack('!HH', data[5:])
                self.server_ip = addr[0]
                print(f"Received offer from {self.server_ip}")  # with port from server
                self.state = "Speedtest"
                break

    def send_request(self):
        """Send the request for file transfer"""
        request_message = MAGIC_COOKIE + struct.pack('B', REQUEST_TYPE) + struct.pack('!Q', self.file_size)
        self.sock_udp.sendto(request_message, (self.server_ip, self.UDP_PORT))

    def handle_udp_transfer(self):
        """UDP transfer function"""
        total_bytes_received = 0
        start_time = time.time()
        current_segment_received = 0
        total_segments = float('inf')

        while current_segment_received < total_segments:
            data, _ = self.sock_udp.recvfrom(BUFFER_SIZE)
            if data.startswith(MAGIC_COOKIE) and data[4] == 0x04:  # Payload message
                total_segments, current_segment_received = struct.unpack('!QQ', data[5:21])
                payload_size = len(data) - 21
                total_bytes_received += payload_size

        total_time = time.time() - start_time
        print(
            f"UDP transfer finished, total time: {total_time:.2f} seconds, total speed: {total_bytes_received * 8 / total_time / 1e6:.2f} Mbits/sec")

    def handle_tcp_transfer(self):
        """Handle the TCP transfer."""
        try:
            self.sock_tcp.connect((self.server_ip, self.TCP_PORT))
            print(f"Connected to server {self.server_ip} on TCP port {self.TCP_PORT}")

            # Send the request message
            request_message = MAGIC_COOKIE + struct.pack('B', REQUEST_TYPE) + struct.pack('!Q', self.file_size)
            self.sock_tcp.send(request_message)

            # Receive data
            total_bytes_received = 0
            start_time = time.time()
            current_segment_received = 0
            total_segments = float('inf')

            while current_segment_received < total_segments:
                data = self.sock_tcp.recv(BUFFER_SIZE)
                if data.startswith(MAGIC_COOKIE) and data[4] == PAYLOAD_TYPE:  # Payload message
                    total_segments, current_segment_received = struct.unpack('!QQ', data[5:21])
                    print(f"total is :{total_segments} and current segment is : {current_segment_received}")
                    payload_size = len(data) - 21
                    total_bytes_received += payload_size
                    print(f"Segment {current_segment_received}/{total_segments} received.")

            total_time = time.time() - start_time
            print(
                f"TCP transfer finished: {total_bytes_received} bytes in {total_time:.2f} seconds, "
                f"speed: {total_bytes_received * 8 / total_time / 1e6:.2f} Mbps"
            )

        except Exception as e:
            print(f"Error during TCP transfer: {e}")
        finally:
            self.sock_tcp.close()
            print("TCP connection closed.")

    def start_speedtest(self):
        """Start the speed test with multiple connections."""
        threads = []

        # Start TCP transfers
        for _ in range(self.num_tcp_connections):
            tcp_thread = Thread(target=self.handle_tcp_transfer)
            tcp_thread.start()
            threads.append(tcp_thread)

        # Start UDP transfers
        for _ in range(self.num_udp_connections):
            udp_thread = Thread(target=self.handle_udp_transfer)
            udp_thread.start()
            threads.append(udp_thread)

        # Wait for all transfers to finish
        for thread in threads:
            thread.join()

        print("All transfers complete, listening for offers...")

    def run(self):
        """main client logic"""
        if self.state == "Startup":
            self.set_parameters()

        if self.state == "Looking for a server":
            self.listen_for_offers()

        if self.state == "Speedtest":
            self.send_request()
            self.start_speedtest()


if __name__ == "__main__":
    client = Client()
    client.run()
