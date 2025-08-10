import json
import mimetypes
import os
import cgi
import re
import io
import shutil
from urllib.parse import urlparse, parse_qsl

from cms_utils.file_system import sanitize_filename, has_valid_extension, MAX_FILE_SIZE, is_image_file, is_valid_image
from logs.activities_operations import insert_activity
from routes.base_handler import BaseHandler
from cms_utils.file_system import get_directory_structure

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
        if parsed_url.path == "/api/cms01/files/list":
            user = self._api_get_authenticated_user_jwt()
            if user:
                files = os.listdir("static/images")
                file_info = []
                for file in files:
                    file_path = os.path.join("static/images", file)
                    mime_type = mimetypes.guess_type(file_path)
                    file_size = os.path.getsize(file_path) if os.path.isfile(file_path) else 0
                    file_info.append({
                        "name": file,
                        "mime_type": mime_type or "unknown",
                        "size": file_size
                    })
                # response = {"files": file_info}
                self.send_json_response({
                    "success": True,
                    "message": "File list",
                    "files": file_info
                }, 200)
                return
            else:
                self.send_json_response({
                    "success": False,
                    "message": "Unauthorized"
                })

        # list all pages
        if parsed_url.path == "/api/cms/files/list":
            user = self._api_get_authenticated_user_jwt()
            if user:
                if user["user_id"]:
                    files_directory = "static/images"
                    if os.path.exists(files_directory) and os.path.isdir(files_directory):
                        directory_structure = get_directory_structure(files_directory)
                        self.send_json_response({
                            "success": True,
                            "message": "Directory structure",
                            "structure": directory_structure
                        }, 200)
                    else:
                        self.send_json_response({
                            "success": False,
                            "message": "Pages directory not found"
                        }, 404)
            else:
                self.send_json_response({
                    "success": False,
                    "message": "Unauthorized"
                }, 403)
            return


    def do_POST(self):
        parsed_url = urlparse(self.path)
        content_type = self.headers.get('Content-Type')
        content_length = int(self.headers.get('Content-Length', 0))
        if not content_type.startswith('multipart/form-data'):
            post_data = self.rfile.read(content_length).decode('utf-8')
            if self.headers.get('Content-Type') == "application/json":
                post_params = json.loads(post_data)
            else:
                post_params = dict(parse_qsl(post_data))

        if parsed_url.path == "/api/cms01/files/upload":
            content_type = self.headers.get("Content-Type", "")

            if "multipart/form-data" in content_type:
                form = cgi.FieldStorage(fp=self.rfile, headers=self.headers, environ={"REQUEST_METHOD": "POST"})

                uploaded_file = form["file"]
                if uploaded_file.filename:
                    save_path = os.path.join("static/images", uploaded_file.filename)

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


        # upload a file
        if parsed_url.path == "/api/cms/files/upload":
            user = self._api_get_authenticated_user_jwt()
            if not user:
                self.send_json_response({
                    "success": False,
                    "message": "Unauthorized"
                }, 403)
                return
            content_type = self.headers.get("Content-Type", "")

            if "multipart/form-data" in content_type:
                content_length = int(self.headers.get("Content-Length", 0))
                if content_length == 0:
                    self.send_json_response({
                        "success": False,
                        "message": "Empty request body"
                    }, 400)
                    return
                body = self.rfile.read(content_length)
                if b"filename=" not in body:
                    self.send_json_response({
                        "success": False,
                        "message": "No files provided in form-data"
                    }, 400)
                    return
                form = cgi.FieldStorage(fp=io.BytesIO(body), headers=self.headers, environ={"REQUEST_METHOD": "POST"})
                # print(form)
                if "files[]" in form and "selected_directory" in form:
                    # change code to accept multiple files
                    files = form["files[]"]
                    selected_directory = form["selected_directory"].value
                    print(selected_directory)
                    print(type(selected_directory))
                    if not isinstance(files, list):
                        files = [files]
                    upload_results = []
                    os.makedirs("static/images", exist_ok=True)
                    for uploaded_file in files:
                        print("c")
                        if uploaded_file.filename:
                            filename = sanitize_filename(uploaded_file.filename)
                            if not has_valid_extension(filename):
                                upload_results.append({
                                    "success": False,
                                    "message": "Invalid file extension",
                                    "filename": filename
                                })
                                continue
                            file_data = uploaded_file.file.read()
                            uploaded_file.file.seek(0)
                            if len(file_data) > MAX_FILE_SIZE:
                                upload_results.append({
                                    "success": False,
                                    "message": "File is too large (max 10MB)",
                                    "filename": filename
                                })
                                continue
                            if not is_image_file(file_data):
                                upload_results.append({
                                    "success": False,
                                    "message": "Only image files are allowed (invalid MIME type)",
                                    "filename": filename
                                })
                                continue
                            if not is_valid_image(file_data):
                                upload_results.append({
                                    "success": False,
                                    "message": "Corroupred or invalid image file",
                                    "filename": filename
                                }, 400)
                                continue
                            if ".." in selected_directory or os.path.isabs(selected_directory):
                                self.send_json_response({
                                    "success": False,
                                    "message": "Invalid target directory"
                                })
                                return
                            save_dir = os.path.join("static/images/", selected_directory)
                            os.makedirs(save_dir, exist_ok=True)
                            save_path = os.path.join(save_dir, filename)
                            with open(save_path, "wb") as f:
                                f.write(file_data)
                            upload_results.append({
                                "success": True,
                                "message": "Uploaded successfully",
                                "filename": filename
                            })
                        else:
                            upload_results.append({
                                "filename": "unknown",
                                "success": False,
                                "message": "No filename"
                            })
                    self.send_json_response({
                        "success": True,
                        "message": "Files uploaded successfully",
                        "results": upload_results
                    }, 200)
                else:
                    self.send_json_response({
                        "success": False,
                        "message": "No files part in the request"
                    }, 400)
            else:
                self.send_json_response({
                    "success": False,
                    "message": "Invalid content type"
                }, 400)

        elif parsed_url.path == "/api/cms/files/delete" and self.command == "POST":
            user = self._api_get_authenticated_user_jwt()
            if user:
                content_length = int(self.headers.get("Content-Length", 0))
                body = self.rfile.read(content_length)
                try:
                    data = json.loads(body)
                    filename = data.get("filename")
                except Exception as e:
                    self.send_json_response({
                        "success": False,
                        "message": f"Invalid JSON: {str(e)}"
                    }, 400)
                    return
                if filename:
                    safe_name = os.path.basename(filename)
                    file_path = os.path.join("static/images", safe_name)
                    if os.path.exists(file_path):
                        try:
                            os.remove(file_path)
                            self.send_json_response({
                                "success": True,
                                "message": f"Deleted '{safe_name}'"
                            }, 200)
                        except Exception as e:
                            self.send_json_response({
                                "success": False,
                                "message": f"Failed to delete file: {str(e)}"
                            }, 500)
                    else:
                        self.send_json_response({
                            "success": False,
                            "message": "File not found"
                        }, 404)
                        return
                else:
                    self.send_json_response({
                        "success": False,
                        "message": "Filename is required"
                    }, 400)
                    return
            else:
                self.send_json_response({
                    "success": False,
                    "message": "Unauthorized"
                }, 403)
                return

        elif parsed_url.path == "/api/cms/files/dir/create":
            print("a")
            user = self._api_get_authenticated_user_jwt()
            if user:
                print("b")
                # length = int(self.headers.get('Content-Length', 0))
                print("c")
                # body = self.rfile.read(length)
                print("d")
                try:
                    # print(body)
                    # data = json.loads(body)
                    #  print(data)
                    dir_name = post_params.get("dir_name")
                    print(dir_name)
                    if dir_name:
                        if not ".." in dir_name and not os.path.isabs(dir_name):
                            target_path = os.path.join("static/images", dir_name)
                            if not os.path.exists(target_path):
                                os.makedirs(target_path)
                                self.send_json_response({
                                    "success": True,
                                    "message": f"Directory '{dir_name}' created"
                                }, 201)
                            else:
                                self.send_json_response({
                                    "success": False,
                                    "message": f"Directory '{dir_name}' already exists"
                                }, 409)
                        else:
                            self.send_json_response({
                                "success": False,
                                "message": "Invalid directory name"
                            }, 400)
                            return
                    else:
                        self.send_json_response({
                            "success": False,
                            "message": "Directory name is required"
                        }, 400)
                        return
                except json.JSONDecodeError:
                    self.send_json_response({
                        "success": False,
                        "message": "Invalid JSON"
                    }, 400)
            else:
                self.send_json_response({
                    "success": False,
                    "message": "Unauthorized"
                }, 401)

        elif parsed_url.path == "/api/cms/files/dir/delete":
            print("a")
            user = self._api_get_authenticated_user_jwt()
            if user:
                raw_dir_name = post_params.get("dir_name")
                if raw_dir_name:
                    sanitized_dir_name = re.sub(r"[^\w/-]", "", raw_dir_name).lstrip("/").strip()
                    if sanitized_dir_name and len(sanitized_dir_name) < 255:
                        pages_root = os.path.abspath("static/images")
                        dir_path = os.path.abspath(os.path.join(pages_root, sanitized_dir_name))
                        print(f"Sanitized Directory Name: {sanitized_dir_name}")
                        print(f"Directory Path: {dir_path}")
                        print(f"Pages Root: {pages_root}")
                        if dir_path.startswith(pages_root + os.sep):
                            if os.path.isdir(dir_path):
                                try:
                                    shutil.rmtree(dir_path)
                                except OSError as e:
                                    self.send_json_response({
                                        "success": False,
                                        "message": f"Error deleting directory: {str(e)}"
                                    }, 500)
                                    return
                                insert_activity(user["email"], "delete", f"Delete directory '{sanitized_dir_name}'")
                                self.send_json_response({
                                    "success": True,
                                    "message": f"Directory '{sanitized_dir_name}' deleted successfully"
                                }, 200)
                                return
                            else:
                                self.send_json_response({
                                    "success": False,
                                    "message": "Directory not found"
                                }, 404)
                                return
                        else:
                            self.send_json_response({
                                "success": False,
                                "message": "Invalid directory path"
                            }, 400)
                            return
                    else:
                        self.send_json_response({
                            "success": False,
                            "message": "Invalid directory name"
                        }, 400)
                        return
                else:
                    self.send_json_response({
                        "success": False,
                        "message": "Missing 'dir_name' in request"
                    }, 400)
                    return
            else:
                self.send_json_response({
                    "success": False,
                    "message": "Unauthorized"
                }, 403)
                return

    def do_DELETE(self):
        parsed_url = urlparse(self.path)
        delete_match = re.match(r"^/api/cms/files/delete/([\w\.-]+)$", parsed_url.path)
        if delete_match:
            filename = delete_match.group(1)
            file_path = os.path.join("static/images", filename)

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