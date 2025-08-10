import json
import os.path
import xml.etree.ElementTree as ET
from distutils.command.install_egg_info import safe_name
from urllib.parse import urlparse, parse_qsl
from routes.base_handler import BaseHandler


class APICMSPagesEditorHandler(BaseHandler):
    def do_POST(self):
        parsed_url = urlparse(self.path)
        content_length = int(self.headers.get('Content-Length', 0))
        post_data = self.rfile.read(content_length).decode('utf-8')
        if self.headers.get('Content-Type') == "application/json":
            post_params = json.loads(post_data)
        else:
            post_params = dict(parse_qsl(post_data))

        if parsed_url.path == "/api/cms/pages/editor/page/get":
            user = self._api_get_authenticated_user_jwt()
            if user and user.get("user_id"):
                try:
                    page_name = post_params.get("page")
                except Exception:
                    self.send_json_response({
                        "success": False,
                        "message": "Invalid JSON body"
                    }, 400)
                    return
                if page_name:
                    file_path = os.path.join("pages", f"{page_name}.xml")
                    if os.path.exists(file_path):
                        try:
                            tree = ET.parse(file_path)
                            root = tree.getroot()
                            def xml_to_dict(element):
                                d = {}
                                for child in element:
                                    child_value = xml_to_dict(child) if len(child) > 0 else child.text
                                    if child.tag in d:
                                        if not isinstance(d[child.tag], list):
                                            d[child.tag] = [d[child.tag]]
                                        d[child.tag].append(child_value)
                                    else:
                                        d[child.tag] = child_value
                                return d
                            page_data = xml_to_dict(root)
                            self.send_json_response({
                                "success": True,
                                "message": "Page data loaded",
                                "page": page_data
                            }, 200)
                        except Exception as e:
                            self.send_json_response({
                                "success": False,
                                "message": f"Failed to parse page XML: {str(e)}"
                            }, 500)
                        return
                    else:
                        self.send_json_response({
                            "success": False,
                            "message": f"Page '{page_name}' not found"
                        }, 404)
                        return
                else:
                    self.send_json_response({
                        "success": False,
                        "message": "Page name not provided"
                    }, 400)
                    return
            else:
                self.send_json_response({
                    "success": False,
                    "message": "Unauthorized"
                }, 403)
                return
        elif parsed_url.path == "/api/cms/pages/editor/component/get":
            user = self._api_get_authenticated_user_jwt()
            if user and user.get("user_id"):
                try:
                    component_name = post_params.get("component")
                except Exception:
                    self.send_json_response({
                        "success": False,
                        "message": "Invalid JSON body"
                    }, 400)
                    return
                if component_name:
                    file_path = os.path.join("pages", "__components__", f"{component_name}.xml")
                    if os.path.exists(file_path):
                        try:
                            tree = ET.parse(file_path)
                            root = tree.getroot()
                            def xml_to_dict(element):
                                d = {}
                                for child in element:
                                    if len(child) > 0:
                                        if child.tag in d:
                                            if isinstance(d[child.tag], list):
                                                d[child.tag].append(xml_to_dict(child))
                                            else:
                                                d[child.tag] = [d[child.tag], xml_to_dict(child)]
                                        else:
                                            d[child.tag] = xml_to_dict(child)
                                    else:
                                        d[child.tag] = child.text
                                return d
                            component_data = xml_to_dict(root)
                            self.send_json_response({
                                "success": True,
                                "message": "Component data loaded",
                                "component": component_data
                            }, 200)
                        except Exception as e:
                            self.send_json_response({
                                "success": False,
                                "message": f"Failed to parse component XML: {str(e)}"
                            }, 500)
                        return
                    else:
                        self.send_json_response({
                            "success": False,
                            "message": f"Component '{component_name}' not found"
                        }, 404)
                        return
                else:
                    self.send_json_response({
                        "success": False,
                        "message": "Component name not provided"
                    }, 400)
                    return
            else:
                self.send_json_response({
                    "success": False,
                    "message": "Unauthorized"
                }, 403)
                return
        elif parsed_url.path == "/api/cms/pages/editor/component/update":
            user = self._api_get_authenticated_user_jwt()
            if user and user.get("user_id"):
                try:
                    # post_params = json.loads(self.rfile.read(int(self.headers['Content-length'])))
                    component_name = post_params.get("component")
                    component_data = post_params.get("data")
                except (json.JSONDecodeError, KeyError, ValueError):
                    self.send_json_response({
                        "success": False,
                        "message": "Invalid JSON body"
                    }, 400)
                    return

                if not component_name:
                    self.send_json_response({
                        "success": False,
                        "message": "Component name not provided"
                    }, 400)
                    return

                if not isinstance(component_data, dict):
                    self.send_json_response({
                        "success": False,
                        "message": "Component data must be an object"
                    }, 400)
                    return

                safe_name = os.path.basename(component_name)
                file_path = os.path.join("pages", "__components__", f"{safe_name}.xml")

                # import xml.etree.ElementTree as ET

                def dict_to_xml(tag, d):
                    elem = ET.Element(tag)
                    for key, val in d.items():
                        if isinstance(val, list):
                            for item in val:
                                elem.append(dict_to_xml(key, item if isinstance(item, dict) else {key: item}))
                        elif isinstance(val, dict):
                            elem.append(dict_to_xml(key, val))
                        else:
                            child = ET.Element(key)
                            child.text = str(val) if val is not None else ""
                            elem.append(child)
                    return elem
                try:
                    root_tag = "component"
                    root_elem = dict_to_xml(root_tag, component_data)
                    os.makedirs(os.path.dirname(file_path), exist_ok=True)
                    tree = ET.ElementTree(root_elem)
                    tree.write(file_path, encoding="utf-8", xml_declaration=True)
                    self.send_json_response({
                        "success": True,
                        "message": f"Component '{component_name}' updated successfully"
                    }, 200)
                except Exception as e:
                    self.send_json_response({
                        "success": False,
                        "message": f"Failed to update component XML: {str(e)}"
                    }, 500)
                return
            else:
                self.send_json_response({
                    "success": False,
                    "message": "Unauthorized"
                }, 403)
                return
        else:
            self.send_json_response({
                "success": False,
                "message": "Invalid request"
            }, 400)