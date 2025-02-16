import http.server
import json

class BaseHandler(http.server.SimpleHTTPRequestHandler):
    def send_json_response(self, data, status_code=200):
        self.send_response(status_code)
        self.send_header("Content-type", "application/json")
        self.end_headers()
        self.wfile.write(json.dumps(data).encode("utf-8"))

    def redirect(self, new_url: str):
        self.send_response(302)
        self.send_header("Location", new_url)
        self.end_headers()