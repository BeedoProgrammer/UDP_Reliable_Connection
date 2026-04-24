import socket
import json
import random

class rdt_UDP():

    SYN    = 0b00000001
    SYNACK = 0b00000011
    ACK    = 0b00000010
    FIN    = 0b00000100

    def __init__(self):
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.seq_num = 0
        self.state = "CLOSED"
        self.socket.settimeout(2.0)

    def rdt_send(self, data, IP_address, port):
        # --- Step 1: Handshake (SYN) ---
        # data is empty during handshake, just sending SYN flag
        bin_data = self.text_to_bin(data)
        checksum = self.find_checksum(bin_data, 8)
        msg = self.make_pckt(self.seq_num, data, checksum, flags=rdt_UDP.SYN)
        string_msg = json.dumps(msg)

        while True:
            self.socket.sendto(string_msg.encode('utf-8'), (IP_address, port))
            try:
                ack, addr = self.socket.recvfrom(1024)
                if self.isACK(ack, self.seq_num):
                    self.state = "OPEN"
                    self.seq_num += 1
                    break
            except socket.timeout:
                print("SYN timeout, resending...")

        # --- Step 2: Send actual data (ACK flag) ---
        if self.state == "OPEN":
            bin_data = self.text_to_bin(data)
            checksum = self.find_checksum(bin_data, 8)
            msg = self.make_pckt(self.seq_num, data, checksum, flags=rdt_UDP.ACK)
            string_msg = json.dumps(msg)

            while True:
                self.socket.sendto(string_msg.encode('utf-8'), (IP_address, port))


                # --- START OF INJECTED TESTS ---

                #test_msg = msg.copy() 
                
                # ----- To test corruption, uncomment ONE of these lines: -------

                #test_msg = self.simulate_false_checksum(test_msg)
                #test_msg = self.simulate_packet_corruption(test_msg)
                
                #string_msg_to_send = json.dumps(test_msg)

                # -----To test loss, it only sends if the function returns False (not lost)------

                #if not self.simulate_packet_loss(0.3):
                #    self.socket.sendto(string_msg_to_send.encode('utf-8'), (IP_address, port))

                # --- END OF INJECTED TESTS ---



                try:
                    ack, addr = self.socket.recvfrom(1024)
                    if self.isACK(ack, self.seq_num):
                        self.seq_num += 1
                        break
                except socket.timeout:
                    print("Data timeout, resending...")

            # --- Step 3: Close connection (FIN) ---
            # Send FIN with empty data
            bin_data = self.text_to_bin("")
            checksum = self.find_checksum(bin_data, 8)
            msg = self.make_pckt(self.seq_num, "", checksum, flags=rdt_UDP.FIN)
            string_msg = json.dumps(msg)

            while True:
                self.socket.sendto(string_msg.encode('utf-8'), (IP_address, port))
                try:
                    ack, addr = self.socket.recvfrom(1024)
                    if self.isACK(ack, self.seq_num):
                        self.state = "CLOSED"
                        self.seq_num += 1
                        break
                except socket.timeout:
                    print("FIN timeout, resending...")

    def rdt_rcv(self):
        # --- Step 1: Receive SYN, send SYNACK ---
        while True:
            try:
                data, addr = self.socket.recvfrom(1024)
                packet = json.loads(data.decode('utf-8'))

                # drop corrupted packets
                if self.is_corrupt(data):
                    print("Corrupt packet dropped")
                    continue

                if packet["flags"] == rdt_UDP.SYN:
                    # send SYNACK back
                    bin_data = self.text_to_bin("")
                    checksum = self.find_checksum(bin_data, 8)
                    msg = self.make_pckt(self.seq_num, "", checksum, flags=rdt_UDP.SYNACK)
                    self.socket.sendto(json.dumps(msg).encode('utf-8'), addr)
                    self.state = "OPEN"
                    self.seq_num += 1
                    break

            except socket.timeout:
                print("Waiting for SYN...")

        # --- Step 2: Receive data, send ACK ---
        while True:
            try:
                data, addr = self.socket.recvfrom(1024)
                packet = json.loads(data.decode('utf-8'))

                if self.is_corrupt(data):
                    print("Corrupt packet dropped")
                    continue

                if packet["flags"] == rdt_UDP.ACK:
                    received_data = packet["data"]  # actual data is here
                    # send ACK back
                    bin_data = self.text_to_bin("")
                    checksum = self.find_checksum(bin_data, 8)
                    msg = self.make_pckt(self.seq_num, "", checksum, 
                                        flags=rdt_UDP.ACK)
                    self.socket.sendto(json.dumps(msg).encode('utf-8'), addr)
                    self.seq_num += 1
                    break

            except socket.timeout:
                print("Waiting for data...")

        # --- Step 3: Receive FIN, send ACK ---
        while True:
            try:
                data, addr = self.socket.recvfrom(1024)
                packet = json.loads(data.decode('utf-8'))

                if self.is_corrupt(data):
                    print("Corrupt packet dropped")
                    continue

                if packet["flags"] == rdt_UDP.FIN:
                    # send ACK back to close
                    bin_data = self.text_to_bin("")
                    checksum = self.find_checksum(bin_data, 8)
                    msg = self.make_pckt(self.seq_num, "", checksum, flags=rdt_UDP.ACK)
                    self.socket.sendto(json.dumps(msg).encode('utf-8'), addr)
                    self.state = "CLOSED"
                    self.seq_num += 1
                    break

            except socket.timeout:
                print("Waiting for FIN...")

        return received_data

    def make_pckt(self, seq_num, data, checksum, flags):
        packet = {
            "seq": seq_num,
            "flags": flags,
            "checksum": checksum,
            "data": data
        }
        return packet

    def isACK(self, received_packet, seq_num):
        packet = json.loads(received_packet.decode('utf-8'))

        is_ack_flag = (packet["flags"] == rdt_UDP.ACK or packet["flags"] == rdt_UDP.SYNACK)
        if is_ack_flag and packet["seq"] == seq_num:
            return True
        else:
            return False

    def is_corrupt(self, received_packet):
        packet = json.loads(received_packet.decode('utf-8'))

        bin_data = self.text_to_bin(packet["data"])
        recalculated = self.find_checksum(bin_data, 8)

        if packet["checksum"] == recalculated:
            return False  # not corrupted
        else:
            return True   # corrupted
        
   # convert text to binary string
    def text_to_bin(self, text):
        # Handle empty strings (like in SYN, SYNACK, FIN, ACK)
        if text == "":
            return "0" * 32
            
        binary = ''.join(format(ord(c), '08b') for c in text)
        # pad to multiple of 32 bits (4 x 8-bit chunks)
        while len(binary) % 32 != 0:
            binary += '0'
        return binary

    def find_checksum(self, data, k):
        # data must be a binary string, padded to 4*k bits
        c1 = data[0:k]
        c2 = data[k:2*k]
        c3 = data[2*k:3*k]
        c4 = data[3*k:4*k]

        Sum = bin(int(c1, 2)+int(c2, 2)+int(c3, 2)+int(c4, 2))[2:]

        if(len(Sum) > k):
            x = len(Sum)-k
            Sum = bin(int(Sum[0:x], 2)+int(Sum[x:], 2))[2:]
        if(len(Sum) < k):
            Sum = '0'*(k-len(Sum))+Sum

        checksum = ''
        for i in Sum:
            if(i == '1'):
                checksum += '0'
            else:
                checksum += '1'
        return checksum

    def check_checksum(self, data, k, checksum):
        c1 = data[0:k]
        c2 = data[k:2*k]
        c3 = data[2*k:3*k]
        c4 = data[3*k:4*k]

        receiver_sum = bin(int(c1, 2)+int(c2, 2)+int(c3, 2)+
                           int(c4, 2)+int(checksum, 2))[2:]

        if(len(receiver_sum) > k):
            x = len(receiver_sum)-k
            receiver_sum = bin(int(receiver_sum[0:x], 2)+int(receiver_sum[x:], 2))[2:]

        receiver_checksum = ''
        for i in receiver_sum:
            if(i == '1'):
                receiver_checksum += '0'
            else:
                receiver_checksum += '1'

        # if all 1s → no corruption
        return receiver_checksum == '1' * k
    
    def bind(self, IP_address, port):
        self.socket.bind((IP_address, port))

    def simulate_packet_loss(self, probability):
        # returns True if packet should be dropped
        if random.random() < probability:
            print("Packet lost!")
            return True
        else:
            return False

    def simulate_packet_corruption(self, packet):
        # flips data to garbage
        packet["data"] = "00000000" * 4
        print("Packet corrupted!")
        return packet

    def simulate_false_checksum(self, packet):
        # replaces checksum with wrong value
        packet["checksum"] = "00000000"
        print("False checksum injected!")
        return packet