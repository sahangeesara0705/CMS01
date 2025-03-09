import jwt
import datetime
import hashlib
import uuid
from urllib.parse import urlparse, parse_qs
import sessions.session_operations
from routes.base_handler import BaseHandler

JWT_SECRET_KEY = "cms01"

class APIAuthHandler(BaseHandler):
    def do_POST(self):
        parsed_url = urlparse(self.path)
        content_length = int(self.headers.get('Content-Length', 0))
        post_data = self.rfile.read(content_length) if content_length > 0 else b""
        post_params = parse_qs(post_data.decode('utf-8')) if post_data else {}

        if parsed_url.path == "/api/auth/register":
            name = post_params.get("name", [""])[0].strip()
            email = post_params.get("email", [""])[0].strip()
            password = post_params.get("password", [""])[0].strip()

            if not name or not email or not password:
                self.send_json_response({
                    "success": False,
                    "message": "Required parameters missing"
                })
                return

            password_hash = hashlib.sha256(password.encode()).hexdigest()

            user_id = str(uuid.uuid4())

            avatar_url = "abc" # hardcode for now
            id = sessions.session_operations.set_user(
                user_id, name, email, password_hash, avatar_url, "Email", "", ""
            )

            if id:
                self.send_json_response({
                    "success": True,
                    "cookie": "User created successfully"
                })
            else:
                self.send_json_response({
                    "success": False,
                    "cookie": "User already exists"
                })

        elif parsed_url.path == "/api/auth/login":
            email = post_params.get("email", [""])[0].strip()
            password = post_params.get("password", [""])[0].strip()

            if not email or not password:
                self.send_json_response({
                    "success": False,
                    "message": "Missing email or password"
                })
                return

            password_hash = hashlib.sha256(password.encode()).hexdigest()

            user = sessions.session_operations.get_user_by_email_and_password(email, password_hash)

            if not user:
                self.send_json_response({
                    "success": False,
                    "message": "Invalid username or password"
                })
                return

            user_id, name, profile_image_url = user

            payload = {
                "user_id": user_id,
                "email": email,
                "name": name,
                "profile_image_url": profile_image_url,
                "exp": datetime.datetime.utcnow() + datetime.timedelta(hours=1)
            }
            token = jwt.encode(payload, JWT_SECRET_KEY, algorithm="HS256")

            self.send_json_response({
                "success": True,
                "message": "Authentication successful",
                "token": token
            })

        elif parsed_url.path == "/api/auth/logout":
            return self._api_logout_jwt()