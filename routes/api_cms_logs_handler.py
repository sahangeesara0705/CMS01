import html
import re
import os
import json
import shutil
from urllib.parse import urlparse, parse_qs, parse_qsl
from routes.base_handler import BaseHandler
from cms_utils.file_system import get_directory_structure
from logs.activities_operations import get_activities

class APICMSLogsHandler(BaseHandler):
    def do_GET(self):
        parsed_url = urlparse(self.path)

        # list all pages
        if parsed_url.path == "/api/cms/logs/activities/list":
            user = self._api_get_authenticated_user_jwt()
            if user:
                activities = get_activities()
                #send activities in a json response
                self.send_json_response({
                    "success": True,
                    "activities": activities,
                    "message": "Activities fetched successfully"
                })
            else:
                self.send_json_response({
                    "success": False,
                    "message": "Unauthorized"
                }, 403)
            return

        # fallback
        self.send_json_response({
            "success": False,
            "message": "Invalid request"
        }, 400)