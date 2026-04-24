from UDP_Reliable import rdt_UDP

class http_client:
    def __init__(self):
        self.rdt_UDP = rdt_UDP()
        self.request = ""
        self.response = ""
        self.client_ip = "127.0.0.1"
        self.client_port = 6666
        self.connect_to_server()
    
    def get(self, host, port, path):
        self.build_get_request(host, path)
        self.rdt_UDP.rdt_send(self.request, host, port) # send request to server
        raw_response, _ = self.rdt_UDP.rdt_rcv() # get server response
        status_code, status_msg = self.parse_response(raw_response)
        print(f"Status Code: {status_code}, Status Message: {status_msg}")
        print(f"Response Body: {self.response}")

    def post(self, host, port, path, body):
        self.build_post_request(host, path, body)
        self.rdt_UDP.rdt_send(self.request, host, port) # send request to server
        raw_response, _ = self.rdt_UDP.rdt_rcv() # get server response
        status_code, status_msg = self.parse_response(raw_response)
        print(f"Status Code: {status_code}, Status Message: {status_msg}")
        print(f"{self.response}")

    def connect_to_server(self):
        self.rdt_UDP.bind(self.client_ip, self.client_port)

    def build_get_request(self, host, path):
        self.request = f"""GET {path} HTTP/1.0\r\nHost: {host}\r\n\r\n"""
        
    def build_post_request(self, host, path, body):
        content_type = "text/html" if path.endswith(".html") else "text/plain"
        self.request = (
                        f"POST {path} HTTP/1.0\r\n"
                        f"Host: {host}\r\n"
                        f"Content-Type: {content_type}\r\n"
                        f"Content-Length: {len(body)}\r\n"
                        f"\r\n"
                        f"{body}"
                    )
    
    def parse_response(self, raw):
        # split header and body
        if "\r\n\r\n" in raw:
            header, body = raw.split("\r\n\r\n", 1)
        else:
            header, body = raw, ""
        self.response = body
        status_code = header.splitlines()[0].split()[1]
        status_msg =  " ".join(header.splitlines()[0].split()[2:])
        return status_code, status_msg
    

client = http_client()
client.get("127.0.0.1", 5555, "/index.html")

# client.post("127.0.0.1", 5555, "/test2.txt", "hello world")