import hashlib
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

router = APIRouter()

# In-memory user store for testing (in production, use a database)
USERS = {
    "test": "password",
    "rafael": "rafael123",
    "heloisa": "heloisa123",
    "demo": "demo",
}

# In-memory token store (simple mock; in production, use JWT)
TOKENS = {}


class LoginRequest(BaseModel):
    username: str
    password: str


class LoginResponse(BaseModel):
    token: str
    username: str


def generate_token(username: str) -> str:
    """Generate a simple token (in production, use JWT)."""
    return hashlib.sha256(f"{username}:{hash(username)}".encode()).hexdigest()


@router.post("/login")
def login(body: LoginRequest):
    """Authenticate user and return token."""
    if body.username not in USERS or USERS[body.username] != body.password:
        raise HTTPException(401, "Invalid username or password")

    token = generate_token(body.username)
    TOKENS[token] = body.username

    return LoginResponse(token=token, username=body.username)


@router.post("/logout")
def logout():
    """Logout user (no-op for this simple implementation)."""
    return {"status": "logged out"}


@router.get("/me")
def get_current_user(token: str = None):
    """Get current user info from token."""
    if not token or token not in TOKENS:
        raise HTTPException(401, "Invalid or missing token")

    username = TOKENS[token]
    return {"username": username}
