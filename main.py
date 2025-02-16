import http.server
import os
from http.cookies import SimpleCookie
import server.serve_html
import user_management.github_oauth_handler
import user_management.x_oauth_handler
import sessions.session_operations
from urllib.parse import urlparse, parse_qs, unquote_plus

PORT = 8000

class MainHandler(http.server.SimpleHTTPRequestHandler):
    def do_GET(self):
        parsed_url = urlparse(self.path)
        query_params = parse_qs(parsed_url.query)

        if parsed_url.path == "/user/login":
            cookie_header = self.headers.get('Cookie')
            session_id = sessions.session_operations.get_session_from_cookies(cookie_header)
            if session_id:
                session_data = sessions.session_operations.get_session(session_id)
                if session_data:
                    self.send_response(302)
                    self.send_header("Content-type", "text/html")
                    self.send_header("Location", "/welcome")
                    self.end_headers()
            else:
                server.serve_html.serve_html_template(self, "cms_templates/login.html", {
                    "github_authentication_url": "/user/login/github",
                    "x_authentication_url": "/user/login/x"
                })
            return
        if parsed_url.path == "/user/logout":
            cookie = SimpleCookie()
            cookie["session_id"] = ""
            cookie["session_id"]["path"] = "/"
            cookie["session_id"]["httponly"] = True
            self.send_response(303)
            self.send_header("Content-type", "text/html")
            self.send_header("Set-Cookie", cookie.output(header=""))
            self.send_header("Location", "/user/login")
            self.end_headers()
            return
        elif parsed_url.path == "/user/login/github":
            github_authentication_url = user_management.github_oauth_handler.get_authorization_url()
            self.redirect(github_authentication_url)
            return
        elif parsed_url.path == "/user/login/x":
            x_authentication_url = user_management.x_oauth_handler.get_authorization_url()
            self.redirect(x_authentication_url)
            return
        elif parsed_url.path == "/user/oauth/github/callback":
            access_token = user_management.github_oauth_handler.get_access_token(query_params.get("code", [""])[0])
            user_data = user_management.github_oauth_handler.get_user_data(access_token)
            user_id = user_data["id"]
            screen_name = user_data["login"]
            name = user_data["name"]
            avatar_url = user_data["avatar_url"]

            cookie = sessions.session_operations.set_session(user_id, access_token, "", screen_name,
                                                             name, avatar_url)

            self.send_response(302)
            self.send_header("Content-type", "text/html")
            self.send_header("Set-Cookie", cookie.output(header=""))
            self.send_header("Location", "/welcome")
            self.end_headers()
            return
        elif parsed_url.path == "/user/oauth/x/callback":
            user_data = user_management.x_oauth_handler.get_user_data(self, query_params)
            user_id = user_data["user_id"]
            access_token = user_data["access_token"]
            access_token_secret = user_data["access_token_secret"]
            screen_name = user_data["screen_name"]
            name = user_data["name"]
            avatar_url = user_data["profile_image_url"]

            cookie = sessions.session_operations.set_session(user_id, access_token, access_token_secret, screen_name, name, avatar_url)

            self.send_response(302)
            self.send_header("Content-type", "text/html")
            self.send_header("Set-Cookie", cookie.output(header=""))
            self.send_header("Location", "/welcome")
            self.end_headers()
            return
        elif parsed_url.path == "/welcome":
            cookie_header = self.headers.get('Cookie')
            session_id = sessions.session_operations.get_session_from_cookies(cookie_header)
            if session_id:
                session_data = sessions.session_operations.get_session(session_id)
                name = session_data[5]
                avatar_url = session_data[6]
                server.serve_html.serve_html_template(self, "cms_templates/welcome.html",
                                                      {"name": name, "avatar_url": avatar_url})
                return
            else:
                self.send_response(302)
                self.send_header("Content-type", "text/html")
                self.send_header("Location", "/user/login")
                self.end_headers()
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