import hashlib
import secrets

def hash_password(password: str) -> str:
    """Creates a secure salt + hash for the password."""
    salt = secrets.token_hex(8)
    hash_obj = hashlib.sha256(f"{salt}{password}".encode())
    return f"{salt}${hash_obj.hexdigest()}"

def verify_password(stored_password: str, provided_password: str) -> bool:
    """Verifies a provided password against the salt$hash stored in DB."""
    try:
        salt, hashed = stored_password.split("$")
        hash_obj = hashlib.sha256(f"{salt}{provided_password}".encode())
        return hash_obj.hexdigest() == hashed
    except (ValueError, AttributeError):
        return False