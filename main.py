import http.server
import os
import server.serve_html
import user_management.github_oauth_handler
import user_management.x_oauth_handler
from urllib.parse import urlparse, parse_qs, unquote_plus

PORT = 8000

class MainHandler(http.server.SimpleHTTPRequestHandler):
    def do_GET(self):
        parsed_url = urlparse(self.path)
        query_params = parse_qs(parsed_url.query)

        if parsed_url.path == "/login":
            github_authentication_url = user_management.github_oauth_handler.get_authorization_url()
            # x_authentication_url = user_management.x_oauth_handler.get_authorization_url()
            server.serve_html.serve_html_template(self, "cms_templates/login.html", {
                "github_authentication_url": github_authentication_url,
                "x_authentication_url": "/login/x"
            })
            return
        elif parsed_url.path == "/login/x":
            x_authentication_url = user_management.x_oauth_handler.get_authorization_url()
            self.redirect(x_authentication_url)
            return
        elif parsed_url.path == "/callback":
            print("1")
            access_token = user_management.github_oauth_handler.get_access_token(query_params.get("code", [""])[0])
            user_data = user_management.github_oauth_handler.get_user_data(access_token)
            name = user_data["name"]
            avatar_url = user_data["avatar_url"]

            self.send_response(200)
            self.send_header("Content-type", "text/html")
            self.end_headers()

            html_form = f"""
            <html>
                <body onload="document.forms[0].submit()">
                    <form action="/welcome" method="POST">
                        <input type="hidden" name="name" value="{name}">
                        <input type="hidden" name="avatar_url" value="{avatar_url}">
                    </form>
                </body>
            </html>
            """
            self.wfile.write(html_form.encode("utf-8"))
            print("2")
            return
        elif parsed_url.path == "/x_callback":
            print("1")
            # access_token = user_management.github_oauth_handler.get_access_token(query_params.get("code", [""])[0])
            user_data = user_management.x_oauth_handler.get_user_data(self, query_params)
            name = user_data["name"]
            avatar_url = user_data["profile_image_url"]

            self.send_response(200)
            self.send_header("Content-type", "text/html")
            self.end_headers()

            html_form = f"""
            <html>
                <body onload="document.forms[0].submit()">
                    <form action="/welcome" method="POST">
                        <input type="hidden" name="name" value="{name}">
                        <input type="hidden" name="avatar_url" value="{avatar_url}">
                    </form>
                </body>
            </html>
            """
            self.wfile.write(html_form.encode("utf-8"))
            print("2")
            return
        elif parsed_url.path == "/":
            self.path = "templates/index.html"
        return super().do_GET()

    def do_POST(self):
        if self.path == "/welcome":
            content_length = int(self.headers["Content-Length"])
            post_data = self.rfile.read(content_length).decode("utf-8")

            parsed_data = parse_qs(post_data)
            name = parsed_data.get("name", [""])[0]
            avatar_url = parsed_data.get("avatar_url", [""])[0]

            name = unquote_plus(name)
            avatar_url = unquote_plus(avatar_url)

            server.serve_html.serve_html_template(self, "cms_templates/welcome.html", {"name": name, "avatar_url": avatar_url})

    def redirect(self, new_url: str):
        self.send_response(302)
        self.send_header("Location", new_url)
        self.end_headers()

os.chdir(os.path.dirname(os.path.abspath(__file__)))

if __name__ == "__main__":
    server_address = ("", PORT)
    httpd = http.server.HTTPServer(server_address, MainHandler)
    print(f"Serving on port: {PORT}...")
    httpd.serve_forever()