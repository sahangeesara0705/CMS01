import os

def serve_html_template(self, file: str, variables: dict):
    file_path = os.path.join(os.getcwd(), file)
    if not os.path.exists(file_path):
        raise FileNotFoundError(f"File '{file}' not found.")

    if not isinstance(variables, dict):
        raise TypeError("Expected a dictionary for variables.")

    try:
        with open(file, "r", encoding="utf-8") as html_file:
            html_template = html_file.read()
    except:
        raise FileNotFoundError(f"File '{file}' not found.")

    for key, value in variables.items():
        if not isinstance(key, str) or not isinstance(value, str):
            raise ValueError("Keys and values in variables must be strings.")
        html_template = html_template.replace("{{" + key + "}}", value)

    self.send_response(200)
    self.send_header("Content-type", "text/html")
    self.end_headers()
    self.wfile.write(html_template.encode("utf-8"))