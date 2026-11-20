import http.server
import socketserver
import urllib.request
import json

PORT = 8047
UPSTREAM = "http://127.0.0.1:20128"

class AntigravityHandler(http.server.SimpleHTTPRequestHandler):
    def do_POST(self):
        content_length = int(self.headers.get('Content-Length', 0))
        body = self.rfile.read(content_length)
        req = urllib.request.Request(
            f"{UPSTREAM}{self.path}",
            data=body,
            headers={key: value for key, value in self.headers.items() if key.lower() != 'host'},
            method='POST'
        )
        try:
            with urllib.request.urlopen(req) as response:
                self.send_response(response.status)
                for header, value in response.headers.items():
                    if header.lower() not in ['transfer-encoding', 'content-encoding']:
                        self.send_header(header, value)
                self.end_headers()
                self.wfile.write(response.read())
        except Exception as e:
            self.send_response(500)
            self.end_headers()
            self.wfile.write(json.dumps({"error": str(e)}).encode())

    def do_GET(self):
        req = urllib.request.Request(
            f"{UPSTREAM}{self.path}",
            headers={key: value for key, value in self.headers.items() if key.lower() != 'host'}
        )
        try:
            with urllib.request.urlopen(req) as response:
                self.send_response(response.status)
                for header, value in response.headers.items():
                    if header.lower() not in ['transfer-encoding', 'content-encoding']:
                        self.send_header(header, value)
                self.end_headers()
                self.wfile.write(response.read())
        except Exception as e:
            self.send_response(500)
            self.end_headers()
            self.wfile.write(json.dumps({"error": str(e)}).encode())

if __name__ == "__main__":
    with socketserver.TCPServer(("", PORT), AntigravityHandler) as httpd:
        print(f"Antigravity-9Router Bridge running on port {PORT}")
        httpd.serve_forever()
