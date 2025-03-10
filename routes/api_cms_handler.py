import html
import re
import os
import mimetypes
from urllib.parse import urlparse, parse_qs
from routes.base_handler import BaseHandler

class APICMSHandler(BaseHandler):
    def do_GET(self):
        parsed_url = urlparse(self.path)
        if parsed_url.path == "/api/cms/welcome":
            name, avatar_url = self._get_authenticated_user() # TODO - need to change to api
            if name:
                self.send_json_response({
                    "success": True,
                    "name": name,
                    "avatar_url": avatar_url,
                    "message": f"Welcome, {name}!"
                }, 200)
            return
        elif parsed_url.path == "/api/cms/list_pages":
            name, avatar_url = self._get_authenticated_user() # TODO - need to change to api

            if name:
                pages_directory = "pages"

                if os.path.exists(pages_directory) and os.path.isdir(pages_directory):
                    pages = [
                        file for file in os.listdir(pages_directory)
                        if file.endswith(".html") and os.path.isfile(os.path.join(pages_directory, file))
                    ]
                    self.send_json_response({"pages": pages}, 200)
                else:
                    self.send_json_response({
                        "success": False,
                        "message": "Pages directory not found"
                    }, 404)
            else:
                self.send_json_response({
                    "success": False,
                    "message": "Unauthorized"
                }, 403)

            return

        if parsed_url.path == "/api/cms/list_files":
            files = os.listdir("uploads")
            file_info = []

            for file in files:
                file_path = os.path.join("uploads", file)
                mime_type = mimetypes.guess_type(file_path)
                file_size = os.path.getsize(file_path) if os.path.isfile(file_path) else 0

                file_info.append({
                    "name": file,
                    "mime_type": mime_type or "unknown",
                    "size": file_size
                })

            response = {"files": file_info}
            self.send_json_response(response, 200)
            return

        self.send_json_response({
            "success": False,
            "message": "Page not found"
        }, 404)

    def do_POST(self):
        parsed_url = urlparse(self.path)

        if parsed_url.path == "/api/cms/edit/new_page":
            name, avatar_url = self._get_authenticated_user() # TODO - need to change to api

            if name:
                content_length = int(self.headers.get("Content-Length", 0))
                post_data = self.rfile.read(content_length)
                form = parse_qs(post_data.decode("utf-8"))

                if "page_name" in form:
                    raw_page_name = form["page_name"][0].strip()
                    page_name = re.sub(r"[^\w-]", "", raw_page_name)

                    if not page_name:
                        self.send_error(400, "Invalid page name")
                        self.send_json_response({
                            "success": False,
                            "message": "Invalid page name"
                        }, 400)
                        return

                    page_path = f"pages/{page_name}.html"

                    if not os.path.exists(page_path):
                        os.makedirs(os.path.dirname(page_path), exist_ok=True)
                        default_content = "<html><head><title>New page</title></head><body><h1>Welcome!</h1></body></html>"
                        with open(page_path, "w", encoding="utf-8", newline="\n") as file:
                            file.write(default_content)

                        self.send_json_response({
                            "success": True,
                            "page_name": page_name,
                            "message": f"Page {page_name} created successfully"
                        }, 200)
                        return
                    else:
                        self.send_json_response({
                            "success": False,
                            "page_name": page_name,
                            "message": f"Page {page_name} already exists"
                        }, 409)
                else:
                    self.send_error(400, "Missing 'page_number' in request")
                    self.send_json_response({
                        "success": False,
                        "message": "Missing 'page_name' in request"
                    }, 409)
                return

        edit_match = re.match(r"^/api/cms/edit/([\w-]+)\.html", parsed_url.path)
        if edit_match:
            page_name = edit_match.group(1)
            name, avatar_url = self._get_authenticated_user() # TODO - need to change to api

            if name:
                page_path = f"pages/{page_name}.html"

                if os.path.exists(page_path):
                    content_length = int(self.headers.get('Content-Length', 0))
                    post_data = self.rfile.read(content_length)
                    form = parse_qs(post_data.decode("utf-8"))

                    if "html_code" in form:
                        html_code = form["html_code"][0]

                        with open(page_path, "w", encoding="utf-8", newline="\n") as file:
                            normalized_html = "\n".join(html_code.splitlines()).strip()
                            decoded_html = html.unescape(normalized_html)
                            file.write(decoded_html)

                        self.send_json_response({
                            "success": True,
                            "message": f"Page {page_name} updated successfully"
                        }, 200)
                        return
                    else:
                        self.send_json_response({
                            "success": False,
                            "message": "Invalid request: Missing 'html_code'"
                        }, 400)
                else:
                    self.send_json_response({
                        "success": False,
                        "message": f"Page '{page_name}' not found"
                    }, 404)
            else:
                self.send_json_response({
                    "success": False,
                    "message": "Unauthorized"
                }, 403)
        else:
            self.send_json_response({
                "success": False,
                "message": "Page not found"
            }, 404)

    def do_DELETE(self):
        parsed_url = urlparse(self.path)
        delete_match = re.match(r"^/api/cms/delete/([\w-]+)\.html$", parsed_url.path)
        if delete_match:
            page_name = delete_match.group(1)
            name, avatar_url = self._get_authenticated_user() # TODO - need to change to api

            if name:
                page_path = f"pages/{page_name}.html"

                if os.path.exists(page_path):
                    try:
                        os.remove(page_path)
                        self.send_json_response({
                            "success": True,
                            "message": "Page deleted successfully"
                        })
                    except Exception as e:
                        self.send_json_response({
                            "success": False,
                            "message": f"Error deleting page: {str(e)}"
                        }, 500)
                else:
                    self.send_json_response({
                        "success": False,
                        "message": f"Page '{page_name}' not found"
                    }, 404)
                return
        self.send_json_response({
            "success": False,
            "message": "Invalid request"
        })