import math
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


class Client:
    def __init__(self):
        self.file_size = 0
        self.server_ip = None
        self.UDP_PORT = None
        self.TCP_PORT = None
        self.num_tcp_connections = 0
        self.num_udp_connections = 0
        self.state = "Startup"

    def set_parameters(self):
        """Ask user for parameters"""
        while True:
            try:
                print(Colors.OKCYAN + "Enter the parameters for the speed test:" + Colors.ENDC)
                self.file_size = int(input("Enter the file size (in bytes): "))
                self.num_tcp_connections = int(input("Enter the number of TCP connections: "))
                self.num_udp_connections = int(input("Enter the number of UDP connections: "))
                if self.file_size >= 0 or self.num_tcp_connections >= 0 or self.num_udp_connections >= 0:
                    break

            except ValueError:
                print(Colors.WARNING + "Invalid input, please try again." + Colors.ENDC)

        self.state = "Looking for a server"

    def listen_for_offers(self):
        """Listen for offer requests and select the first server found"""
        udp_socket = socket(AF_INET, SOCK_DGRAM)
        udp_socket.bind(('', 9876))
        print(Colors.OKBLUE + "Client started, listening for offer requests..." + Colors.ENDC)

        while True:
            data, addr = udp_socket.recvfrom(BUFFER_SIZE)
            if data.startswith(MAGIC_COOKIE) and struct.unpack('B', data[4:5])[0] == OFFER_TYPE:  # Offer message
                self.UDP_PORT, self.TCP_PORT = struct.unpack('!HH', data[5:])
                self.server_ip = addr[0]
                print(Colors.OKGREEN + f"Received offer from {self.server_ip}" + Colors.ENDC)  # with port from server
                self.state = "Speedtest"
                break

    def handle_udp_transfer(self, num_thread):
        sock_udp = socket(AF_INET, SOCK_DGRAM)
        sock_udp.settimeout(120)
        try:
            """UDP transfer function"""
            request_message = MAGIC_COOKIE + struct.pack('B', REQUEST_TYPE) + struct.pack('!Q', self.file_size)
            sock_udp.sendto(request_message, (self.server_ip, self.UDP_PORT))

            total_bytes_received = 0
            current_segment_received = 0
            total_segments = float('inf')
            start_time = time.time()
            problem = False

            while current_segment_received < total_segments:
                try:
                    data, _ = sock_udp.recvfrom(BUFFER_SIZE)
                    if data.startswith(MAGIC_COOKIE) and data[4] == 0x04:  # Payload message
                        total_segments, current_segment_received = struct.unpack('!QQ', data[5:21])
                        payload_size = len(data) - 21
                        total_bytes_received += payload_size
                except timeout:
                    problem = True
                    print(Colors.FAIL + f"UDP transfer #{num_thread} timeout: No data received for 5 seconds." + Colors.ENDC)
                    break

            if not problem:
                total_time = time.time() - start_time
                print(
                    Colors.OKGREEN +
                    f"UDP transfer #{num_thread} finished, {total_bytes_received} bytes in {total_time:.2f} seconds, "
                    f"speed: {total_bytes_received * 8 / (total_time + 0.000001):.2f} bits/second.\n"
                    f"percentage of packets received successfully: {total_bytes_received / self.file_size * 100:.2f}%\n"
                    + Colors.ENDC
                )

        except Exception as e:
            print(Colors.FAIL + f"Error during UDP transfer #{num_thread}: {e}" + Colors.ENDC)
        finally:
            sock_udp.close()

    def handle_tcp_transfer(self, num_thread):
        """Handle the TCP transfer."""
        sock_tcp = socket(AF_INET, SOCK_STREAM)
        try:
            sock_tcp.connect((self.server_ip, self.TCP_PORT))

            file_size = str(self.file_size) + '\n'
            sock_tcp.send(file_size.encode())

            total_bytes_received = 0
            current_segment_received = 0
            total_segments = math.ceil(self.file_size / BUFFER_SIZE)
            start_time = time.time()

            while current_segment_received < total_segments:
                data = sock_tcp.recv(BUFFER_SIZE)
                payload_size = len(data)
                total_bytes_received += payload_size
                current_segment_received += 1

            total_time = time.time() - start_time
            print(
                Colors.OKGREEN +
                f"TCP transfer #{num_thread} finished, {total_bytes_received} bytes in {total_time:.2f} seconds, "
                f"speed: {total_bytes_received * 8 / (total_time + 0.000001):.2f} bits/second.\n"
                f"percentage of packets received successfully: {total_bytes_received / self.file_size * 100:.2f}%\n"
                + Colors.ENDC
            )
        except Exception as e:
            print(Colors.FAIL + f"Error during TCP transfer #{num_thread}: {e}" + Colors.ENDC)
        finally:
            sock_tcp.close()

    def start_speedtest(self):
        """Start the speed test with multiple connections."""
        threads = []

        # Start TCP transfers
        for i in range(self.num_tcp_connections):
            tcp_thread = Thread(target=self.handle_tcp_transfer(i), name=f"TCP-{i}")
            tcp_thread.start()
            threads.append(tcp_thread)

        # Start UDP transfers
        for i in range(self.num_udp_connections):
            udp_thread = Thread(target=self.handle_udp_transfer(i), name=f"UDP-{i}")
            udp_thread.start()
            threads.append(udp_thread)

        # Wait for all transfers to finish
        for thread in threads:
            thread.join()

        print(Colors.OKCYAN + "All transfers complete, listening to offer requests." + Colors.ENDC)

    def run(self):
        """Main client logic"""
        if self.state == "Startup":
            self.set_parameters()

        if self.state == "Looking for a server":
            self.listen_for_offers()

        if self.state == "Speedtest":
            self.start_speedtest()
            self.state = "Looking for a server"


if __name__ == "__main__":
    client = Client()
    while True:
        client.run()
        time.sleep(1)
