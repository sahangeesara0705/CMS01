import html
import json
import re
import os
from urllib.parse import urlparse, parse_qs
import server.serve_html
from routes.base_handler import BaseHandler

class CMSHandler(BaseHandler):
    def do_GET(self):
        parsed_url = urlparse(self.path)
        query_params = parse_qs(parsed_url.query)
        if parsed_url.path == "/cms/welcome":
            name, avatar_url = self._get_authenticated_user()
            if name:
                server.serve_html.serve_html_template(self, "cms_templates/welcome.html", {
                    "name": name,
                    "avatar_url": avatar_url
                })
            return
        elif parsed_url.path == "/cms/cms_templates/css/styles.css":
            self.path = "cms_templates/css/styles.css"
            return
        elif parsed_url.path == "/cms/edit/new_page":
            name, avatar_url = self._get_authenticated_user()
            if name:
                server.serve_html.serve_html_template(self, "cms_templates/edit/new_page.html", {
                    "name": name,
                    "avatar_url": avatar_url,
                    "page_content": ""
                })
            return
        edit_match = re.match(r"^/cms/edit/([\w-]+)\.html$", parsed_url.path)
        if edit_match:
            page_name = edit_match.group(1)
            name, avatar_url = self._get_authenticated_user()
            if name:
                # if {page_name}.html file exists in "/pages" get content to a variable
                page_path = f"pages/{page_name}.html"

                if os.path.exists(page_path):
                    with open(page_path, "r", encoding="utf-8") as file:
                        page_content = file.read()

                    page_content = "\n".join(page_content.splitlines()).strip()
                    encoded_html = html.escape(page_content)

                    server.serve_html.serve_html_template(self, "cms_templates/edit/edit_page.html", {
                        "page_name": page_name,
                        "name": name,
                        "avatar_url": avatar_url,
                        "page_content": encoded_html,
                        "edit_path": f"/cms/edit/{page_name}.html"
                    })
                else:
                    self.send_response(404, f"Page {page_name} not found")
            return

        error_message = b"<html><body><h1>404 Not Found</h1><p>Page not found.</p></body></html>"
        self.send_response(404)
        self.send_header("Content-type", "text/html")
        self.send_header("Content-Length", str(len(error_message)))
        self.end_headers()
        self.wfile.write(error_message)

    def do_POST(self):
        parsed_url = urlparse(self.path)

        if parsed_url.path == "/cms/edit/new_page":
            content_length = int(self.headers.get("Content-Length", 0))
            post_data = self.rfile.read(content_length)
            form = parse_qs(post_data.decode("utf-8"))

            if "page_name" in form:
                raw_page_name = form["page_name"][0].strip()
                page_name = re.sub(r"[^\w-]", "", raw_page_name)

                if not page_name:
                    self.send_error(400, "Invalid page name")
                    return

                page_path = f"pages/{page_name}.html"

                if not os.path.exists(page_path):
                    os.makedirs(os.path.dirname(page_path), exist_ok=True)

                    default_content = "<html><head><title>New page</title></head><body><h1>Welcome!</h1></body></html>"

                    with open(page_path, "w", encoding="utf-8", newline="\n") as file:
                        file.write(default_content)

                    self.redirect(f"/cms/edit/{page_name}.html")
                    return
                else:
                    self.send_error(409, "Page already exists")
            else:
                self.send_error(400, "Missing 'page_number' in request")
            return
        edit_match = re.match(r"^/cms/edit/([\w-]+)\.html", parsed_url.path)
        if edit_match:
            # get post data html_code san write it to the file
            page_name = edit_match.group(1)
            name, avatar_url = self._get_authenticated_user()

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

                        self.redirect(f"/cms/edit/{page_name}.html")
                        return
                    else:
                        self.send_error(400, "Invalid request: Missing 'html_code'")
                else:
                    self.send_error(404, f"Page '{page_name}' not found")
            else:
                self.send_error(403, "Unauthorized")