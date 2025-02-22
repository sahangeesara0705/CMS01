import re
import os
from urllib.parse import urlparse, parse_qs
import sessions.session_operations
import server.serve_html
from routes.base_handler import BaseHandler

class CMSHandler(BaseHandler):
    def _get_authenticated_user(self):
        """Retrieve user data from session or redirect if unauthorized."""
        cookie_header = self.headers.get('Cookie')
        session_id = sessions.session_operations.get_session_from_cookies(cookie_header)

        if session_id:
            user_data = sessions.session_operations.get_user_by_session_id(session_id)
            return user_data[2], user_data[3]

        self.send_response(302)
        self.send_header("Content-type", "text/html")
        self.send_header("Location", "/user/login")
        self.end_headers()
        return None, None

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
                    server.serve_html.serve_html_template(self, "cms_templates/edit/edit_page.html", {
                        "page_name": page_name,
                        "name": name,
                        "avatar_url": avatar_url,
                        "page_content": page_content,
                        "edit_path": f"/cms/edit/{page_name}.html"
                    })
                else:
                    self.send_response(404, f"Page {page_name} not found")
            return

        self.send_response(404)
        self.send_header("Content-type", "text/html")
        self.end_headers()
        self.wfile.write(b"Page not found")

    def do_POST(self):
        parsed_url = urlparse(self.path)

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
                            file.write(html_code.replace("\r\n", "\n"))

                        server.serve_html.serve_html_template(self, "cms_templates/edit/edit_page.html", {
                            "page_name": page_name,
                            "name": name,
                            "avatar_url": avatar_url,
                            "page_content": html_code,
                            "edit_path": f"/cms/edit/{page_name}.html"
                        })

                        return

                        self.send_response(200)
                        self.send_header("Content-Type", "application/json")
                        self.end_headers()
                        self.wfile.write(b'{"status": "success", "message": "Page updated successfully"}')
                    else:
                        self.send_error(400, "Invalid request: Missing 'html_code'")
                else:
                    self.send_error(404, f"Page '{page_name}' not found")
            else:
                self.send_error(403, "Unauthorized")