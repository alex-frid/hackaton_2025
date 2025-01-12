from socket import *
import threading
import struct
import time

# Const
UDP_PORT = 27069
TCP_PORT = 27069
BUFFER_SIZE = 1024
SERVER_IP = '10.202.66.20'
MAGIC_COOKIE = b'\xAB\xCD\xDC\xBA'  # Magic cookie
REQUEST_TYPE = 0x03  # request message type


class Client:
    def __init__(self):
        self.file_size = 0
        self.server_ip = None
        self.state = "Startup"

    def set_parameters(self):
        """ask user for parameters"""
        self.file_size = int(input("Enter the file size (in bytes): "))
        self.state = "Looking for a server"


    def listen_for_offers(self):
        """listen for offer requests and select the first server found"""
        udp_socket = socket(AF_INET, SOCK_DGRAM)
        udp_socket.bind(('', UDP_PORT))
        print("Client started, listening for offer requests...")

        while True:
            data, addr = udp_socket.recvfrom(BUFFER_SIZE)
            if data.startswith(MAGIC_COOKIE) and data[4] == 0x02:  # Offer message
                self.server_ip = addr[0]
                print(f"Received offer from {self.server_ip}")
                self.state = "Speedtest"
                break

    def send_request(self):
        """Send the request for file transfer"""
        udp_socket = socket(AF_INET, SOCK_DGRAM)
        request_message = MAGIC_COOKIE + struct.pack('B', REQUEST_TYPE) + struct.pack('!Q', self.file_size)
        udp_socket.sendto(request_message, (self.server_ip, UDP_PORT))

    def handle_udp_transfer(self):
        """UDP transfer function"""
        udp_socket = socket(AF_INET, SOCK_DGRAM)
        total_bytes_received = 0
        total_segments = (self.file_size + BUFFER_SIZE - 1) // BUFFER_SIZE
        segments_received = 0
        start_time = time.time()

        while total_bytes_received < self.file_size:
            data, _ = udp_socket.recvfrom(BUFFER_SIZE)
            if data.startswith(MAGIC_COOKIE) and data[4] == 0x04:  # Payload message
                total_segments, current_segment = struct.unpack('!QQ', data[5:13])
                payload_size = len(data) - 13
                total_bytes_received += payload_size
                segments_received += 1

        total_time = time.time() - start_time
        print(
            f"UDP transfer finished, total time: {total_time:.2f} seconds, total speed: {total_bytes_received * 8 / total_time / 1e6:.2f} Mbits/sec")

    def start_speedtest(self):
        """Start both TCP and UDP transfers"""
        threads = []

        # Start TCP transfer
        #TODO: TCP transfer

        # Start UDP transfer
        udp_thread = threading.Thread(target=self.handle_udp_transfer)
        udp_thread.start()
        threads.append(udp_thread)

        # Wait for all transfers to finish
        for thread in threads:
            thread.join()

        print("All transfers complete, listening for offers...")

    def run(self):
        """Main client logic"""
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
