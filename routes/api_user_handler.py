import jwt
import datetime
import hashlib
import uuid
import json
from urllib.parse import urlparse, parse_qs, parse_qsl
import sessions.session_operations
from routes.base_handler import BaseHandler

JWT_SECRET_KEY = "cms01"

class APIUserHandler(BaseHandler):
    def do_GET(self):
        parsed_url = urlparse(self.path)
        if parsed_url.path == "/api/users/profiles":
            auth_header = self.headers.get("Authorization")
            if not auth_header or not auth_header.startswith("Bearer "):
                self.send_json_response({
                    "success": False,
                    "message": "Missing or invalid token"
                }, 401)
                return
            token = auth_header.split(" ")[1]
            try:
                payload = jwt.decode(token, JWT_SECRET_KEY, algorithms=["HS256"])
                user_id = payload.get("user_id")
                print(payload)

                user = sessions.session_operations.get_user_by_user_id(user_id)
                if not user:
                    self.send_json_response({
                        "success": False,
                        "message": "User not found"
                    }, 404)
                    return
                id, user_id, name, email, password_hash, profile_image_url, sign_in_type, access_token, access_token_secret = user
                self.send_json_response({
                    "success": True,
                    "user": {
                        "user_id": user_id,
                        "name": name,
                        "email": email,
                        "profile_image_url": profile_image_url
                    }
                })
            except jwt.ExpiredSignatureError:
                self.send_json_response({
                    "success": False,
                    "message": "Token has expired"
                }, 401)
            except jwt.InvalidTokenError:
                self.send_json_response({
                    "success": False,
                    "message": "Invalid token"
                }, 401)
        if parsed_url.path == "/api/users/info":
            auth_header = self.headers.get("Authorization")
            if not auth_header or not auth_header.startswith("Bearer "):
                self.send_json_response({
                    "success": False,
                    "message": "Missing or invalid token"
                }, 401)
                return
            token = auth_header.split(" ")[1]
            try:
                payload = jwt.decode(token, JWT_SECRET_KEY, algorithms=["HS256"])
                user_id = payload.get("user_id")
                name = payload.get("name")
                email = payload.get("email")
                self.send_json_response({
                    "success": True,
                    "user": {
                        "user_id": user_id,
                        "name": name,
                        "email": email
                    }
                })
            except jwt.ExpiredSignatureError:
                self.send_json_response({
                    "success": False,
                    "message": "Token has expired"
                }, 401)
            except jwt.InvalidTokenError:
                self.send_json_response({
                    "success": False,
                    "message": "Invalid token"
                }, 401)
    def do_POST(self):
        parsed_url = urlparse(self.path)
        content_length = int(self.headers.get('Content-Length', 0))
        post_data = self.rfile.read(content_length).decode('utf-8')
        if self.headers.get('Content-Type') == "application/json":
            post_params = json.loads(post_data)
        else:
            post_params = dict(parse_qsl(post_data))
        # post_params = parse_qs(post_data.decode('utf-8')) if post_data else {}