import http.server
import os
from routes.user_handler import UserHandler
from routes.cms_handler import CMSHandler

PORT = 8000

os.chdir(os.path.dirname(os.path.abspath(__file__)))

class MainRouter:
    ROUTES = {
        "/user": UserHandler,
        "/cms": CMSHandler
    }

    def get_handler(self, path):
        for route, handler_class in self.ROUTES.items():
            if path.startswith(route):
                return handler_class
        return None

class RequestDispatcher(http.server.SimpleHTTPRequestHandler):
    def do_GET(self):
        router = MainRouter()
        handler_class = router.get_handler(self.path)
        if handler_class:
            self.protocol_version = "HTTP/1.1"
            self.__class__ = handler_class
            handler_class.do_GET(self)
        elif self.path.startswith("/static/"):
            self.path = self.path.lstrip("/")
            return http.server.SimpleHTTPRequestHandler.do_GET(self)
        else:
            self.send_error(404, "Route not found")

def run_server():
    server_address = ("", PORT)
    httpd = http.server.HTTPServer(server_address, RequestDispatcher)
    print("Server running on port 8000...")
    httpd.serve_forever()

if __name__ == "__main__":
    run_server()