import json
from getpass import getpass

def load_users(file_path):
    with open(file_path, "r") as f:
        return json.load(f)

def login(email, password):
    admins = load_users("admins.json")
    users = load_users("users.json")

    for admin in admins:
        if admin["email"] == email and admin["password"] == password:
            return {"role": "admin", "user": admin}

    for user in users:
        if user["email"] == email and user["password"] == password:
            return {"role": "user", "user": user}

    return None

def is_admin(session):
    return session.get("role") == "admin"

def is_user(session):
    return session.get("role") == "user"