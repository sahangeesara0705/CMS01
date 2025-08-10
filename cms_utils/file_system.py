import os
import cgi
import magic
import mimetypes
from PIL import Image
from io import BytesIO

MAX_FILE_SIZE = 10 * 1024 * 1024
ALLOWED_IMAGE_MIME_TYPES = {
    "image/png", "image/jpg", "image/jpeg", "image/gif", "image/webp", "image/avif", "image/svg+xml"
}
ALLOWED_IMAGE_EXTENSIONS = {"png", "jpg", "jpeg", "gif", "webp", "avif", "svg"}

def get_directory_structure(directory):
    """
    Recursively builds the directory structure with file sizes.
    :param directory:
    :return:
    """
    structure = []
    for root, dirs, files, in os.walk(directory):
        relative_path = os.path.relpath(root, directory)
        if relative_path == ".":
            relative_path = ""

        file_list = [
            {
                "name": file,
                "size": os.path.getsize(os.path.join(root, file)),
                "mime_type": mimetypes.guess_type(os.path.join(root, file))
            }
            for file in files if file.endswith((".html", ".png", ".jpg", ".jpeg", ".pdf"))
        ]

        structure.append({
            "folder": relative_path,
            "files": file_list
        })

    return structure

def is_valid_image(file_data):
    try:
        Image.open(BytesIO(file_data)).verify()
        return True
    except Exception:
        return False

def is_image_file(file_data):
    mime = magic.from_buffer(file_data, mime=True)
    return mime in ALLOWED_IMAGE_MIME_TYPES

def has_valid_extension(file_name):
    ext = os.path.splitext(file_name)[1].lower().lstrip(".")
    return ext in ALLOWED_IMAGE_EXTENSIONS

def sanitize_filename(filename):
    return os.path.basename(filename)