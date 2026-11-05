import hashlib
import hmac
import secrets
import base64

from database import next_id, read_store, save_store
from user_model import User


PASSWORD_ITERATIONS = 310_000


def _validate_credentials(username, password):
    username = username.strip()
    if len(username) < 3 or len(username) > 32:
        print("Username must be between 3 and 32 characters.")
        return False
    if len(password) < 8:
        print("Password must be at least 8 characters.")
        return False
    return True


def _insert_user(store, username, password, role):
    salt = secrets.token_bytes(16)
    password_hash = hashlib.pbkdf2_hmac(
        "sha256", password.encode("utf-8"), salt, PASSWORD_ITERATIONS
    )
    user = {
        "id": next_id(store, "users"),
        "username": username.strip(),
        "password_salt": base64.b64encode(salt).decode("ascii"),
        "password_hash": base64.b64encode(password_hash).decode("ascii"),
        "role": role,
    }
    store["users"].append(user)
    return User(user["id"], user["username"], user["role"])


def _username_exists(store, username):
    return any(
        user["username"].casefold() == username.strip().casefold()
        for user in store["users"]
    )


def create_account(username, password):
    if not _validate_credentials(username, password):
        return None
    store = read_store()
    if _username_exists(store, username):
        print("That username is already in use.")
        return None
    user = _insert_user(store, username, password, "customer")
    save_store(store)
    return user


def has_admin():
    return any(user["role"] == "admin" for user in read_store()["users"])


def create_initial_admin(username, password):
    if not _validate_credentials(username, password):
        return None
    store = read_store()
    if has_admin():
        print("An admin account has already been created.")
        return None
    if _username_exists(store, username):
        print("That username is already in use.")
        return None
    user = _insert_user(store, username, password, "admin")
    save_store(store)
    return user


def sign_in(username, password):
    user = next(
        (
            item
            for item in read_store()["users"]
            if item["username"].casefold() == username.strip().casefold()
        ),
        None,
    )
    if user is None:
        return None

    candidate_hash = hashlib.pbkdf2_hmac(
        "sha256",
        password.encode("utf-8"),
        base64.b64decode(user["password_salt"]),
        PASSWORD_ITERATIONS,
    )
    saved_hash = base64.b64decode(user["password_hash"])
    if not hmac.compare_digest(candidate_hash, saved_hash):
        return None
    return User(user["id"], user["username"], user["role"])