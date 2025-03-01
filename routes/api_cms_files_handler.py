import os
import cgi
import re
from urllib.parse import urlparse
from routes.base_handler import BaseHandler

# TODO authentication

class APICMSFilesHandler(BaseHandler):
    def do_GET(self):
        parsed_url = urlparse(self.path)

        # download a file
        match = re.match(r"^/api/cms/files/download/([\w\.-]+)$", parsed_url.path)
        if match:
            filename = match.group(1)
            file_path = os.path.join("uploads", filename)

            if os.path.exists(file_path):
                self.send_response(200)
                self.send_header("Content-Type", "application/octet-stream")
                self.send_header("Content-Disposition", f"attachment; filename={filename}")
                self.end_headers()

                with open(file_path, "rb") as file:
                    self.wfile.write(file.read())

            else:
                self.send_json_response({
                    "success": False,
                    "message": "File not found"
                }, 404)



        # list files
        if parsed_url.path == "/api/cms/files/list":
            files = os.listdir("uploads")
            response = {"files": files}

            self.send_json_response(response, 200)


    def do_POST(self):
        parsed_url = urlparse(self.path)


        # upload a file
        if parsed_url.path == "/api/cms/files/upload":
            content_type = self.headers.get("Content-Type", "")

            if "multipart/form-data" in content_type:
                form = cgi.FieldStorage(fp=self.rfile, headers=self.headers, environ={"REQUEST_METHOD": "POST"})

                uploaded_file = form["file"]
                if uploaded_file.filename:
                    save_path = os.path.join("uploads", uploaded_file.filename)

                    with open(save_path, "wb") as f:
                        f.write(uploaded_file.file.read())

                    self.send_json_response({
                        "success": True,
                        "message": "File uploaded successfully"
                    }, 200)
                else:
                    self.send_json_response({
                        "success": False,
                        "message": "No file uploaded"
                    }, 400)
            else:
                self.send_json_response({
                    "success": False,
                    "message": "Invalid Content-Type"
                })

    def do_DELETE(self):
        parsed_url = urlparse(self.path)
        delete_match = re.match(r"^/api/cms/files/delete/([\w\.-]+)$", parsed_url.path)
        if delete_match:
            filename = delete_match.group(1)
            file_path = os.path.join("uploads", filename)

            if os.path.exists(file_path):
                try:
                    os.remove(file_path)
                    self.send_json_response({
                        "success": True,
                        "message": "File deleted successfully"
                    })
                except Exception as e:
                    self.send_json_response({
                        "success": False,
                        "message": f"Error deleting file: {str(e)}"
                    }, 500)
            else:
                self.send_json_response({
                    "success": False,
                    "message": f"File '{filename}' not found"
                }, 404)