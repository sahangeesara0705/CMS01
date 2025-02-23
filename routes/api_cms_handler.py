import html
import json
import re
import os
from urllib.parse import urlparse, parse_qs
import server.serve_html
from routes.base_handler import BaseHandler

class APICMSHandler(BaseHandler):
    def do_GET(self):
        parsed_url = urlparse(self.path)
        query_params = parse_qs(parsed_url.query)
        if parsed_url.path == "/api/cms/list_pages":
            name, avatar_url = self._get_authenticated_user()

            if not name:
                self.send_error(403, "Unauthorized")
                return

            pages_directory = "pages"

            if os.path.exists(pages_directory) and os.path.isdir(pages_directory):
                pages = [
                    file for file in os.listdir(pages_directory)
                    if file.endswith(".html") and os.path.isfile(os.path.join(pages_directory, file))
                ]

                self.send_response(200)
                self.send_header("Content-Type", "application/json")
                self.end_headers()
                self.wfile.write(json.dumps({"pages": pages}).encode("utf-8"))
            else:
                self.send_error(404, "Pages directory not found")

            return

        error_message = b"<html><body><h1>404 Not Found</h1><p>Page not found.</p></body></html>"
        self.send_response(404)
        self.send_header("Content-type", "text/html")
        self.send_header("Content-Length", str(len(error_message)))
        self.end_headers()
        self.wfile.write(error_message)