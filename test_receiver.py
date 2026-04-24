from UDP_Reliable import rdt_UDP

print("Starting receiver...")
receiver = rdt_UDP()
receiver.bind('127.0.0.1', 8080)

# This will block and wait for the Sender
final_data = receiver.rdt_rcv()

print(f"\nSUCCESS! Final extracted data: {final_data}")