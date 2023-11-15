import socket, struct, time, random


# Constants
SERVER_ADDRESS = '8.8.8.8'  # Replace with your server's IP
SERVER_PORT = 7  # Replace with your server's port
PACKET_SIZE = 160 # 160
PACKET_COUNT = 20 # 200
TIMEOUT = 1  # Timeout in seconds

# Variables
num_sent = 0
num_received = 0
times = []
latencies = []


def calculate_checksum(source_string):
    count = len(source_string)
    sum = 0
    for index in range(0, count, 2):
        if index + 1 >= count:
            sum += source_string[index]
        else:
            this = source_string[index + 1] * 256 + source_string[index]
            sum += this

    sum &= 0xffffffff  # Truncate sum to 32 bits (a variance from ping.c, which uses signed ints,
                       # but overflow is unlikely in ping)
    sum = (sum >> 16) + (sum & 0xffff)  # Add high 16 bits to low 16 bits
    sum += (sum >> 16)                  # Add carry from above (if any)
    answer = ~sum & 0xffff              # Invert and truncate to 16 bits
    answer = socket.htons(answer)       # Convert to network byte order
    return answer


def create_icmp_packet(num_sent, timestamp):
    TYPE = 8
    CODE = 0
    CHECKSUM = 0
    ID = random.randint(0, 0xFFFF)
    SEQ = num_sent - 1

    header = struct.pack("!BBHHHd", TYPE, CODE, 0, ID, SEQ, timestamp)
    checksum = calculate_checksum(header)
    header = struct.pack("!BBHHHd", TYPE, CODE, checksum, ID, SEQ, timestamp)
    packet = header
    return packet



def ping(destination):

    global num_sent, num_received, times
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM, socket.IPPROTO_ICMP)
    s.settimeout(TIMEOUT)
    # s.setsockopt(socket.SOL_IP, socket.IP_TTL, 64)
    # print(f"PING {destination} with 64 bytes of data:")

    while num_sent < PACKET_COUNT:
        num_sent += 1  # Increment the sent packet counter
        s_timestamp = time.time()
        packet = create_icmp_packet(num_sent, s_timestamp)
        start_time = time.time()
        s.sendto(packet, (destination, 1))

        try:  # ICMP receiving logic here
            data, addr = s.recvfrom(60) # We need max 98 bytes for ICMPv4

            data = data[:60].hex()
            r_header_version = data[0:1]
            r_header_lenght = data[1:2]
            r_total_lenght = int(data[4:8], 16)
            r_identification = int(data[8:12], 16)
            r_flags = data[12:14]
            r_fragment_offset = data[14:16]
            r_ttl = int(data[16:18], 16)
            r_protocol = int(data[18:20], 16)
            r_header_checksum = data[20:24]
            r_source_address = socket.inet_ntoa(bytes.fromhex(data[24:32]))
            r_destination_address = socket.inet_ntoa(bytes.fromhex(data[32:40]))
            r_icmp_type = int(data[40:42], 16)
            r_icmp_code = int(data[42:44], 16)
            r_icmp_checksum = data[44:48]
            r_id = int(data[48:52], 16)
            r_seq = int(data[52:56], 16)
            r_timestamp = int(data[56:64], 16)


            if r_seq == num_sent-1:
                round_trip_time = time.time() - s_timestamp
                latencies.append(round_trip_time)
                times.append(round_trip_time)

                print(f"timestamp: {s_timestamp} r_timestamp: {r_timestamp}")

                print(f"\n{len(data)+14} bytes from {destination}: icmp_seq={r_seq} ttl={r_ttl} time={round_trip_time * 1000:.2f} ms")

                print(f"header_version: {r_header_version}")
                print(f"header_lenght: {r_header_lenght}")
                print(f"total_lenght: {r_total_lenght}")
                print(f"identification: {r_identification}")
                print(f"flags: {r_flags}")
                print(f"fragment_offset: {r_fragment_offset}")
                print(f"ttl: {r_ttl}")
                print(f"protocol: {r_protocol}")
                print(f"header_checksum: {r_header_checksum}")
                print(f"source_address: {r_source_address}")
                print(f"destination_address: {r_destination_address}")
                print(f"icmp_type: {r_icmp_type}")
                print(f"icmp_code: {r_icmp_code}")
                print(f"icmp_checksum: {r_icmp_checksum}")
                print(f"id: {r_id}")
                print(f"seq: {r_seq}")
                print(f"timestamp: {r_timestamp}")

                num_received += 1  # Increment the received packet counter

            else:
                # print("Packet received out of order OR packet loss")
                continue

        except socket.timeout:  # If a timeout exception occurred, then no packet was received
            # print("Request timed out.")
            continue
        time.sleep(0.12)


def main():
    ping(SERVER_ADDRESS)

    # Calculate metrics
    latency_avg = sum(latencies) / len(latencies) if latencies else 0
    packet_loss = (num_sent - num_received) / num_sent
    jitter = sum(abs(latency - latency_avg) for latency in latencies) / len(latencies) if latencies else 0

    # Print results
    print(f"\n--- {SERVER_ADDRESS} ping statistics ---")
    print(f"Latency: {latency_avg * 1000:.2f} ms")
    print(f"Packet Loss: {packet_loss * 100:.2f}%")
    print(f"Jitter: {jitter * 1000:.2f} ms")

if __name__ == "__main__":
    main()