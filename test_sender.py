from UDP_Reliable import rdt_UDP

print("Starting sender...")
sender = rdt_UDP()

# This triggers your 3-way handshake, data transfer, and teardown
sender.rdt_send("HELLO RELIABLE UDP", '127.0.0.1', 8080)

print("\nSUCCESS! Data sent and connection closed.")