from socket import *
from threading import Thread
import struct
import time

# Const
BUFFER_SIZE = 1024
MAGIC_COOKIE = b'\xAB\xCD\xDC\xBA'  # Magic cookie
REQUEST_TYPE = 0x03  # request message type
OFFER_TYPE = 0x02  # offer message type


class Client:
    def __init__(self):
        # TODO: add data struct from holding sockets i.e list
        self.file_size = 0
        self.server_ip = None
        self.UDP_PORT = None
        self.TCP_PORT = None
        self.state = "Startup"
        self.sock_udp = socket(AF_INET, SOCK_DGRAM)

    def set_parameters(self):
        """ask user for parameters"""
        self.file_size = int(input("Enter the file size (in bytes): "))
        self.state = "Looking for a server"
        # TODO: ask for number of TCP/UDP connections

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

    def start_speedtest(self):
        """Start both TCP and UDP transfers"""
        # threads = []
        #
        # # Start TCP transfer
        # # TODO: TCP transfer
        #
        # # Start UDP transfer
        # # TODO: open Thread for each number of socket connections
        # udp_thread = Thread(target=self.handle_udp_transfer)
        # udp_thread.start()
        # threads.append(udp_thread)
        #
        # # Wait for all transfers to finish
        # for thread in threads:
        #     thread.join()
        self.handle_udp_transfer()

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
