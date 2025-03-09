import uuid

def is_valid_uuid(id):
    try:
        uuid_obj = uuid.UUID(id, version=4)
        return str(uuid_obj) == id
    except ValueError:
        return False