import http.server
import json

import jwt

import sessions.session_operations

SECRET_KEY = "cms01"
JWT_BLACKLIST = set()

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

    def _api_get_authenticated_user_jwt(self):
        """Retrieve user data from JWT token or return None if unauthorized."""
        auth_header = self.headers.get("Authorization")
        if not auth_header or not auth_header.startswith("Bearer "):
            return None
        token = auth_header.split(" ")[1]
        if token in JWT_BLACKLIST:
            print("Token is blacklisted")
            return None
        try:
            payload = jwt.decode(token, SECRET_KEY, algorithms=["HS256"])
            user_id = payload.get("user_id")
            email = payload.get("email")
            name = payload.get("name")
            profile_image_url = payload.get("profile_image_url")
            return {
                "user_id": user_id,
                "email": email,
                "name": name,
                "profile_image_url": profile_image_url
            }
        except jwt.ExpiredSignatureError:
            print("JWT token expired")
            return None
        except jwt.InvalidTokenError:
            print("invalid JWT token")
            return None

    def _api_logout_jwt(self):
        """Invalidate JWT token (logout user)"""
        auth_header = self.headers.get("Authorization")
        if not auth_header or not auth_header.startswith("Bearer "):
            self.send_json_response({
                "success": False,
                "message": "No token provided"
            }, 401)
            return
        token = auth_header.split(" ")[1]
        try:
            jwt.decode(token, SECRET_KEY, algorithms=["HS256"])
            JWT_BLACKLIST.add(token)
            self.send_json_response({
                "success": True,
                "message": "Logged out successfully"
            }, 200)
        except jwt.ExpiredSignatureError:
            self.send_json_response({
                "success": False,
                "message": "Token already expired"
            }, 401)
        except jwt.InvalidTokenError:
            self.send_json_response({
                "success": False,
                "message": "Invalid token"
            }, 401)