import html
import re
import os
import json
import shutil
from urllib.parse import urlparse, parse_qs, parse_qsl
from routes.base_handler import BaseHandler
from cms_utils.file_system import get_directory_structure
from logs.activities_operations import insert_activity

class APICMSPagesHandler(BaseHandler):
    def do_GET(self):
        parsed_url = urlparse(self.path)

        # list all pages
        if parsed_url.path == "/api/cms/pages/list":
            user = self._api_get_authenticated_user_jwt()
            if user:
                if user["user_id"]:
                    pages_directory = "pages"
                    if os.path.exists(pages_directory) and os.path.isdir(pages_directory):
                        directory_structure = get_directory_structure(pages_directory)
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


        # get page details
        edit_match = re.match(r"^/api/cms/pages/get/([\w-]+)\.html$", parsed_url.path)
        if edit_match:
            page_name = edit_match.group(1)
            user = self._api_get_authenticated_user_jwt()
            if user:
                page_path = f"pages/{page_name}.html"
                if os.path.exists(page_path):
                    with open(page_path, "r", encoding="utf-8") as file:
                        page_content = file.read()
                    page_content = "\n".join(page_content.splitlines()).strip()
                    encoded_html = html.escape(page_content)
                    self.send_json_response({
                        "success": True,
                        "page_name": page_name,
                        "html_code": page_content,
                        "message": f"Page {page_name} loaded successfully"
                    })
                else:
                    self.send_json_response({
                        "success": False,
                        "message": f"Page {page_name}.html not found"
                    })
            return



        # fallback
        self.send_json_response({
            "success": False,
            "message": "Page not found"
        }, 404)



    def do_POST(self):
        # parsed_url = urlparse(self.path)
        parsed_url = urlparse(self.path)
        content_length = int(self.headers.get('Content-Length', 0))
        post_data = self.rfile.read(content_length).decode('utf-8')
        if self.headers.get('Content-Type') == "application/json":
            post_params = json.loads(post_data)
        else:
            post_params = dict(parse_qsl(post_data))



        # create a new page
        if parsed_url.path == "/api/cms/pages/create/page":
            user = self._api_get_authenticated_user_jwt() # TODO - need to change to api

            if user:
                form = post_params
                print("t")
                print(post_data)
                print(post_params)

                if "page_name" in form:
                    raw_page_name = post_params.get("page_name")
                    if not raw_page_name:
                        self.send_json_response({
                            "success": False,
                            "message": "Missing 'page_name' in request"
                        }, 400)
                        return

                    sanitized_page_name = re.sub(r"[^\w./-]", "", raw_page_name)
                    print(sanitized_page_name)

                    if not sanitized_page_name.endswith(".html") or len(sanitized_page_name) > 255:
                        self.send_json_response({
                            "success": False,
                            "message": "Invalid page name"
                        }, 400)
                        return

                    pages_root = os.path.abspath("pages")
                    page_path = os.path.abspath(os.path.join(pages_root, sanitized_page_name))
                    print(page_path)
                    print(os.path.abspath("pages"))

                    if not page_path.startswith(os.path.abspath("pages")):
                        self.send_json_response({
                            "success": False,
                            "message": "Invalid page path"
                        }, 400)
                        return

                    if os.path.exists(page_path):
                        self.send_json_response({
                            "success": False,
                            "page_name": sanitized_page_name,
                            "message": f"Page '{sanitized_page_name}' already exists"
                        }, 409)
                        return

                    os.makedirs(os.path.dirname(page_path), exist_ok=True)

                    default_content = "<html><head><title>New Page</title></head><body><h1>Welcome!</h1></body></html>"
                    try:
                        with open(page_path, "w", encoding="utf-8", newline="\n") as file:
                            file.write(default_content)
                    except OSError as e:
                        self.send_json_response({
                            "success": False,
                            "message": f"Error creating file: {str(e)}"
                        }, 500)
                        return

                    insert_activity(user["email"], "create", f"Create page '{sanitized_page_name}'")
                    self.send_json_response({
                        "success": True,
                        "page_name": sanitized_page_name,
                        "message": f"Page '{sanitized_page_name}' created successfully"
                    }, 201)
                    return
                else:
                    self.send_json_response({
                        "success": False,
                        "message": "Invalid request"
                    })
                    return
            else:
                self.send_json_response({
                    "success": False,
                    "message": "Unauthorized"
                })
                return

        elif parsed_url.path == "/api/cms/pages/dir/create":
            user = self._api_get_authenticated_user_jwt()

            if user:
                form = post_params

                if "dir_name" in form:
                    raw_dir_name = post_params.get("dir_name")
                    dir_name = re.sub(r"[^\w/-]", "", raw_dir_name)

                    if not dir_name:
                        self.send_error(400, "Invalid directory name")
                        self.send_json_response({
                            "success": False,
                            "message": "Invalid directory name"
                        }, 400)
                        return

                    dir_path = f"pages/{dir_name}"

                    if not os.path.exists(dir_path):
                        os.makedirs(dir_path, exist_ok=True)
                        insert_activity(user["email"], "create", f"Create directory '{dir_name}'")
                        self.send_json_response({
                            "success": True,
                            "dir_name": dir_name,
                            "message": f"Directory {dir_name} created successfully"
                        }, 200)
                        return
                    else:
                        self.send_json_response({
                            "success": False,
                            "dir_name": dir_name,
                            "message": f"Directory {dir_name} already exists"
                        }, 409)
                        return
                else:
                    self.send_json_response({
                        "success": False,
                        "message": "Missing 'dir_name' in request"
                    }, 400)
                    return



        # update a page
        edit_match = re.match(r"^/api/cms/pages/update/([\w-]+)\.html", parsed_url.path)
        if edit_match:
            page_name = edit_match.group(1)
            name, avatar_url = self._get_authenticated_user() # TODO - need to change to api

            if name:
                page_path = f"pages/{page_name}.html"

                if os.path.exists(page_path):
                    content_length = int(self.headers.get('Content-Length', 0))
                    post_data = self.rfile.read(content_length)
                    form = parse_qs(post_data.decode("utf-8"))

                    if "html_code" in form:
                        html_code = form["html_code"][0]

                        with open(page_path, "w", encoding="utf-8", newline="\n") as file:
                            normalized_html = "\n".join(html_code.splitlines()).strip()
                            decoded_html = html.unescape(normalized_html)
                            file.write(decoded_html)

                        self.send_json_response({
                            "success": True,
                            "message": f"Page {page_name} updated successfully"
                        }, 200)
                        return
                    else:
                        self.send_json_response({
                            "success": False,
                            "message": "Invalid request: Missing 'html_code'"
                        }, 400)
                else:
                    self.send_json_response({
                        "success": False,
                        "message": f"Page '{page_name}' not found"
                    }, 404)
            else:
                self.send_json_response({
                    "success": False,
                    "message": "Unauthorized"
                }, 403)



        elif parsed_url.path == "/api/cms/pages/delete/page":
            user = self._api_get_authenticated_user_jwt()

            if user:
                raw_page_name = post_params.get("page_name")
                if raw_page_name:
                    sanitized_page_name = re.sub(r"[^\w./-]", "", raw_page_name).lstrip("/").strip()
                    if sanitized_page_name.endswith(".html") and len(sanitized_page_name) < 255:
                        pages_root = os.path.abspath("pages")
                        page_path = os.path.abspath(os.path.join(pages_root, sanitized_page_name))
                        print(f"Sanitized Page Name: {sanitized_page_name}")
                        print(f"Page Path: {page_path}")
                        print(f"Pages Root: {pages_root}")
                        if page_path.startswith(pages_root + os.sep):
                            if os.path.isfile(page_path):
                                try:
                                    os.remove(page_path)
                                except OSError as e:
                                    self.send_json_response({
                                        "success": False,
                                        "message": f"Error deleting file: {str(e)}"
                                    }, 500)
                                    return
                                insert_activity(user["email"], "delete", f"Delete page '{sanitized_page_name}'")
                                self.send_json_response({
                                    "success": True,
                                    "page_name": sanitized_page_name,
                                    "message": f"Page '{sanitized_page_name}' deleted successfully"
                                }, 200)
                                return
                            else:
                                self.send_json_response({
                                    "success": False,
                                    "message": "Page not found"
                                }, 404)
                                return
                        else:
                            self.send_json_response({
                                "success": False,
                                "message": "Invalid page path"
                            }, 400)
                            return
                    else:
                        self.send_json_response({
                            "success": False,
                            "message": "Invalid page name"
                        }, 400)
                        return
                else:
                    self.send_json_response({
                        "success": False,
                        "message": "Missing 'page_name' in the request"
                    }, 400)
                    return
            else:
                self.send_json_response({
                    "success": False,
                    "message": "Unauthorized"
                }, 403)
                return

        elif parsed_url.path == "/api/cms/pages/dir/delete":
            user = self._api_get_authenticated_user_jwt()
            if user:
                raw_dir_name = post_params.get("dir_name")
                if raw_dir_name:
                    sanitized_dir_name = re.sub(r"[^\w/-]", "", raw_dir_name).lstrip("/").strip()
                    if sanitized_dir_name and len(sanitized_dir_name) < 255:
                        pages_root = os.path.abspath("pages")
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
        elif parsed_url.path == "/api/cms/pages/rename":
            user = self._api_get_authenticated_user_jwt()

            if user:
                form = post_params
                if "page_name" in form and "new_page_name" in form:
                    raw_page_name = post_params.get("page_name")
                    raw_new_page_name = post_params.get("new_page_name")
                    if raw_page_name.endswith(".html") and raw_new_page_name.endswith(".html"):
                        page_name = re.sub(r"[^\w/-]", "", raw_page_name[:-5]) + ".html"
                        new_page_name = re.sub(r"[^\w/-]", "", raw_new_page_name[:-5]) + ".html"
                        if page_name and new_page_name:
                            old_path = f"pages/{page_name}"
                            new_path = f"pages/{new_page_name}"

                            if os.path.exists(old_path):
                                if not os.path.exists(new_path):
                                    os.rename(old_path, new_path)
                                    insert_activity(user["email"], "rename", f"Rename page '{page_name}' to '{new_page_name}'")
                                    self.send_json_response({
                                        "success": True,
                                        "old_page_name": page_name,
                                        "new_page_name": new_page_name,
                                        "message": f"Page '{page_name}' renamed to '{new_page_name}' successfully"
                                    }, 200)
                                    return
                                else:
                                    self.send_json_response({
                                        "success": False,
                                        "message": f"Page '{new_page_name}' already exists"
                                    }, 409)
                                    return
                            else:
                                self.send_json_response({
                                    "success": False,
                                    "message": f"Page '{page_name}' dose not exists"
                                }, 404)
                                return
                        else:
                            self.send_json_response({
                                "success": False,
                                "message": "Invalid page name"
                            }, 400)
                            return
                    else:
                        self.send_json_response({
                            "success": False,
                            "message": "Both 'page_name' and 'new_page_name' must ends with .html"
                        })
                        return
                else:
                    self.send_json_response({
                        "success": False,
                        "message": "Missing 'page_name' or 'new_page_name' in request"
                    }, 400)
                    return
            else:
                self.send_json_response({
                    "success": False,
                    "message": "Unauthorized"
                }, 403)
                return

        elif parsed_url.path == "/api/cms/pages/dir/rename":
            user = self._api_get_authenticated_user_jwt()

            if user:
                form = post_params
                if "dir_name" in form and "new_dir_name" in form:
                    raw_dir_name = post_params.get("dir_name")
                    raw_new_dir_name = post_params.get("new_dir_name")
                    dir_name = re.sub(r"[^\w/-]", "", raw_dir_name)
                    new_dir_name = re.sub(r"[^\w/-]", "", raw_new_dir_name)
                    if dir_name and new_dir_name:
                        old_path = f"pages/{dir_name}"
                        new_path = f"pages/{new_dir_name}"

                        if os.path.exists(old_path):
                            if not os.path.exists(new_path):
                                os.rename(old_path, new_path)
                                insert_activity(user["email"], "rename", f"Rename directory '{dir_name}' to '{new_dir_name}'")
                                self.send_json_response({
                                    "success": True,
                                    "old_dir_name": dir_name,
                                    "new_dir_name": new_dir_name,
                                    "message": f"Directory '{dir_name}' renamed to '{new_dir_name}' successfully"
                                }, 200)
                                return
                            else:
                                self.send_json_response({
                                    "success": False,
                                    "message": f"Directory '{new_dir_name}' already exists"
                                }, 409)
                                return
                        else:
                            self.send_json_response({
                                "success": False,
                                "message": f"Directory '{dir_name}' dose not exist"
                            }, 404)
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
                        "message": "Missing 'dir_name' or 'new_dir_name' in request"
                    }, 400)
                    return
            else:
                self.send_json_response({
                    "success": False,
                    "message": "Unauthorized"
                }, 403)
                return

        self.send_json_response({
            "success": False,
            "message": "Invalid request"
        }, 400)



    # delete a page
    def do_DELETE(self):
        parsed_url = urlparse(self.path)
        delete_match = re.match(r"^/api/cms/pages/delete/([\w-]+)\.html$", parsed_url.path)
        print(delete_match.group(1))
        if delete_match:
            print("a")
            page_name = delete_match.group(1)
            user = self._api_get_authenticated_user_jwt()
            print(user)

            if user:
                print("b")
                page_path = f"pages/{page_name}.html"

                if os.path.exists(page_path):
                    print("c")
                    try:
                        os.remove(page_path)
                        self.send_json_response({
                            "success": True,
                            "message": "Page deleted successfully"
                        })
                    except Exception as e:
                        self.send_json_response({
                            "success": False,
                            "message": f"Error deleting page: {str(e)}"
                        }, 500)
                else:
                    self.send_json_response({
                        "success": False,
                        "message": f"Page '{page_name}' not found"
                    }, 404)
                return
        self.send_json_response({
            "success": False,
            "message": "Invalid request"
        })