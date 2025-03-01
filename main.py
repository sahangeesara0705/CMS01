import http.server
import os
from routes.user_handler import UserHandler
from routes.cms_handler import CMSHandler
from routes.api_cms_handler import APICMSHandler
from routes.api_cms_pages_handler import APICMSPagesHandler

PORT = 8000

os.chdir(os.path.dirname(os.path.abspath(__file__)))

class StaticFileHandler(http.server.SimpleHTTPRequestHandler):
    STATIC_DIR = os.path.abspath("static")

    def translate_path(self, path):
        """Translate URL path to filesystem path, ensuring security."""
        if path.startswith("/static/"):
            path = path[len("/static/"):]
            safe_path = os.path.normpath(os.path.join(self.STATIC_DIR, path))

            print(safe_path)

            if not safe_path.startswith(self.STATIC_DIR):
                self.send_error(403, "Forbidden")
                return None
            return safe_path
        return super().translate_path(path)

class MainRouter:
    ROUTES = {
        "/user": UserHandler,
        "/cms": CMSHandler,
        "/api/cms/pages": APICMSPagesHandler,
        "/api/cms": APICMSHandler
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
            self.__class__ = StaticFileHandler
            StaticFileHandler.do_GET(self)
            # self.path = self.path.lstrip("/")
            # return http.server.SimpleHTTPRequestHandler.do_GET(self)
        else:
            self.send_error(404, "Route not found")

    def do_POST(self):
        router = MainRouter()
        handler_class = router.get_handler(self.path)
        if handler_class:
            self.protocol_version = "HTTP/1.1"
            self.__class__ = handler_class
            handler_class.do_POST(self)
        else:
            self.send_error(405, "Method Not Allowed")

    def do_DELETE(self):
        router = MainRouter()
        handler_class = router.get_handler(self.path)
        if handler_class and hasattr(handler_class, "do_DELETE"):
            self.protocol_version = "HTTP/1.1"
            self.__class__ = handler_class
            handler_class.do_DELETE(self)
        else:
            self.send_error(405, "Method Not Allowed")

def run_server():
    server_address = ("", PORT)
    httpd = http.server.HTTPServer(server_address, RequestDispatcher)
    print("Server running on port 8000...")
    httpd.serve_forever()

if __name__ == "__main__":
    run_server()