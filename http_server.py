from UDP_Reliable import rdt_UDP
from pathlib import Path

class http_server:

    BASE_DIR = Path.cwd()

    def __init__(self):
        self.rdt_UDP = rdt_UDP()
        self.request = ""
        self.response = ""
        self.response_body = ""
        self.response_code = 0
        self.response_msg = ""
        self.content_type = "text/plain"
        self.server_ip = "127.0.0.1"
        self.server_port = 80
        # self.start()
    
    def start(self, server_ip, server_port):
        self.server_ip = server_ip
        self.server_port = server_port
        self.rdt_UDP.bind(server_ip, server_port)
        self.capture_requests()

    def capture_requests(self):
        print(f"HTTP Server running on {self.server_ip}:{self.server_port}")
        while True:
            print("Waiting for incoming requests...")
            self.rdt_UDP.reset()
            self.request, client_addr = self.rdt_UDP.rdt_rcv()
            print(f"Received request from {client_addr}")
            self.handle_request()
            self.build_response()
            self.rdt_UDP.rdt_send(self.response, client_addr[0], client_addr[1])
            print(f"Sent response to {client_addr}\n")

    def handle_request(self):
        self.reset()
        if "\r\n\r\n" in self.request:
            header, body = self.request.split("\r\n\r\n", 1)
        else:
            header, body = self.request, ""
        method  = header.splitlines()[0].split()[0]
        if method  == "GET":
            self.handle_get_request(header)
        elif method  == "POST":
            self.handle_post_request(header, body)

    def handle_get_request(self, header):
        raw_path = header.splitlines()[0].split()[1].lstrip("/")
        file_path = http_server.BASE_DIR / raw_path

        if not file_path.resolve().is_relative_to(http_server.BASE_DIR.resolve()):
            self.response_code = 403
            self.response_msg = "FORBIDDEN"
            return

        if file_path.exists():
            content = file_path.read_text()
            self.content_type = "text/html" if file_path.suffix == ".html" else "text/plain"
            self.response_code = 200
            self.response_msg = "OK"
            self.response_body = content
        else:
            self.response_code = 404
            self.response_msg = "NOT FOUND"
        
    def handle_post_request(self, header, body):
        headers_dict = {}
        for line in header.splitlines()[1:]:
            if ": " in line:
                k, v = line.split(": ", 1)
                headers_dict[k] = v
        
        expected_length = int(headers_dict.get("Content-Length", 0))
        if len(body) != expected_length:
            self.response_code = 400
            self.response_msg = "BAD REQUEST"
            return
        raw_path = header.splitlines()[0].split()[1].lstrip("/")
        file_path = http_server.BASE_DIR / raw_path  # anchor to BASE_DIR too
        file_path.write_text(body)
        self.content_type = "text/html" if file_path.suffix == ".html" else "text/plain"
        self.response_code = 200
        self.response_msg = "OK"

    def build_response(self):
        self.response = (
                        f"HTTP/1.0 {self.response_code} {self.response_msg}\r\n"
                        f"Content-Type: {self.content_type}\r\n"
                        f"Content-Length: {len(self.response_body)}\r\n"
                        f"\r\n" 
                        f"{self.response_body}"
                    )
    def reset(self):
        self.response = ""
        self.response_body = ""
        self.response_code = 0
        self.response_msg = ""
        self.content_type = "text/plain"

server = http_server()
server.start("127.0.0.1", 5555)