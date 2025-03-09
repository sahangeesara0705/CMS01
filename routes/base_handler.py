import http.server
import json
import sessions.session_operations

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

    def _get_authenticated_user(self):
        """Retrieve user data from session or redirect if unauthorized."""
        cookie_header = self.headers.get('Cookie')
        session_id = sessions.session_operations.get_session_from_cookies(cookie_header)

        if session_id:
            user_data = sessions.session_operations.get_user_by_session_id(session_id)

            if user_data:
                return user_data[2], user_data[3]
            else:
                self.send_response(302)
                self.send_header("Content-type", "text/html")
                self.send_header("Location", "/user/login")
                self.end_headers()
                return None, None

        self.send_response(302)
        self.send_header("Content-type", "text/html")
        self.send_header("Location", "/user/login")
        self.end_headers()
        return None, None

    def _api_get_authenticated_user(self):
        """Retrieve user data from session or redirect if unauthorized."""
        cookie_header = self.headers.get('Cookie')
        session_id = sessions.session_operations.get_session_from_cookies(cookie_header)

        if session_id:
            user_data = sessions.session_operations.get_user_by_session_id(session_id)
            print(user_data)

            if user_data:
                return user_data[2], user_data[3]
            else:
                return None, None