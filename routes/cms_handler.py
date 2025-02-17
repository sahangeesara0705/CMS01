from urllib.parse import urlparse, parse_qs
import sessions.session_operations
import server.serve_html
from routes.base_handler import BaseHandler

class CMSHandler(BaseHandler):
    def do_GET(self):
        parsed_url = urlparse(self.path)
        query_params = parse_qs(parsed_url.query)
        if parsed_url.path == "/cms/welcome":
            cookie_header = self.headers.get('Cookie')
            session_id = sessions.session_operations.get_session_from_cookies(cookie_header)
            if session_id:
                user_data = sessions.session_operations.get_user_by_session_id(session_id)
                name = user_data[2]
                avatar_url = user_data[3]
                server.serve_html.serve_html_template(self, "cms_templates/welcome.html",
                                                      {"name": name, "avatar_url": avatar_url})
                return
            else:
                self.send_response(302)
                self.send_header("Content-type", "text/html")
                self.send_header("Location", "/user/login")
                self.end_headers()
                return
        elif parsed_url.path == "/cms/cms_templates/css/styles.css":
            self.path = "cms_templates/css/styles.css"
            return