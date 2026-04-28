"""
High School Management System API

A super simple FastAPI application that allows students to view and sign up
for extracurricular activities at Mergington High School.
"""

from fastapi import Depends, FastAPI, Header, HTTPException
from fastapi.staticfiles import StaticFiles
from fastapi.responses import RedirectResponse
import os
from pathlib import Path
from typing import Optional
import hashlib
import secrets
from pydantic import BaseModel

app = FastAPI(title="Mergington High School API",
              description="API for viewing and signing up for extracurricular activities")


class RegisterRequest(BaseModel):
    email: str
    password: str
    role: str = "student"


class LoginRequest(BaseModel):
    email: str
    password: str

# Mount the static files directory
current_dir = Path(__file__).parent
app.mount("/static", StaticFiles(directory=os.path.join(Path(__file__).parent,
          "static")), name="static")

# In-memory activity database
activities = {
    "Chess Club": {
        "description": "Learn strategies and compete in chess tournaments",
        "schedule": "Fridays, 3:30 PM - 5:00 PM",
        "max_participants": 12,
        "participants": ["michael@mergington.edu", "daniel@mergington.edu"]
    },
    "Programming Class": {
        "description": "Learn programming fundamentals and build software projects",
        "schedule": "Tuesdays and Thursdays, 3:30 PM - 4:30 PM",
        "max_participants": 20,
        "participants": ["emma@mergington.edu", "sophia@mergington.edu"]
    },
    "Gym Class": {
        "description": "Physical education and sports activities",
        "schedule": "Mondays, Wednesdays, Fridays, 2:00 PM - 3:00 PM",
        "max_participants": 30,
        "participants": ["john@mergington.edu", "olivia@mergington.edu"]
    },
    "Soccer Team": {
        "description": "Join the school soccer team and compete in matches",
        "schedule": "Tuesdays and Thursdays, 4:00 PM - 5:30 PM",
        "max_participants": 22,
        "participants": ["liam@mergington.edu", "noah@mergington.edu"]
    },
    "Basketball Team": {
        "description": "Practice and play basketball with the school team",
        "schedule": "Wednesdays and Fridays, 3:30 PM - 5:00 PM",
        "max_participants": 15,
        "participants": ["ava@mergington.edu", "mia@mergington.edu"]
    },
    "Art Club": {
        "description": "Explore your creativity through painting and drawing",
        "schedule": "Thursdays, 3:30 PM - 5:00 PM",
        "max_participants": 15,
        "participants": ["amelia@mergington.edu", "harper@mergington.edu"]
    },
    "Drama Club": {
        "description": "Act, direct, and produce plays and performances",
        "schedule": "Mondays and Wednesdays, 4:00 PM - 5:30 PM",
        "max_participants": 20,
        "participants": ["ella@mergington.edu", "scarlett@mergington.edu"]
    },
    "Math Club": {
        "description": "Solve challenging problems and participate in math competitions",
        "schedule": "Tuesdays, 3:30 PM - 4:30 PM",
        "max_participants": 10,
        "participants": ["james@mergington.edu", "benjamin@mergington.edu"]
    },
    "Debate Team": {
        "description": "Develop public speaking and argumentation skills",
        "schedule": "Fridays, 4:00 PM - 5:30 PM",
        "max_participants": 12,
        "participants": ["charlotte@mergington.edu", "henry@mergington.edu"]
    }
}

# In-memory user and session stores
users = {}
sessions = {}


def hash_password(password: str, salt: Optional[bytes] = None):
    if salt is None:
        salt = os.urandom(16)
    digest = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt, 200_000)
    return salt.hex(), digest.hex()


def verify_password(password: str, salt_hex: str, password_hash: str):
    salt = bytes.fromhex(salt_hex)
    _, candidate_hash = hash_password(password, salt)
    return secrets.compare_digest(candidate_hash, password_hash)


def create_user(email: str, password: str, role: str = "student"):
    if role not in {"student", "admin"}:
        raise HTTPException(status_code=400, detail="Invalid role")

    if len(password) < 8:
        raise HTTPException(status_code=400, detail="Password must be at least 8 characters")

    salt_hex, password_hash = hash_password(password)
    users[email] = {
        "email": email,
        "role": role,
        "salt": salt_hex,
        "password_hash": password_hash,
    }


def extract_bearer_token(authorization: Optional[str]):
    if not authorization or not authorization.startswith("Bearer "):
        return None
    return authorization.split(" ", 1)[1].strip()


def require_authenticated_user(authorization: Optional[str] = Header(default=None)):
    token = extract_bearer_token(authorization)
    if not token or token not in sessions:
        raise HTTPException(status_code=401, detail="Authentication required")

    email = sessions[token]
    user = users.get(email)
    if user is None:
        sessions.pop(token, None)
        raise HTTPException(status_code=401, detail="Invalid session")

    return user


def require_admin_user(current_user=Depends(require_authenticated_user)):
    if current_user["role"] != "admin":
        raise HTTPException(status_code=403, detail="Admin access required")
    return current_user


# Seed demo users so the UI can be exercised immediately.
create_user("admin@mergington.edu", "admin123!", "admin")
create_user("student@mergington.edu", "student123!", "student")


@app.get("/")
def root():
    return RedirectResponse(url="/static/index.html")


@app.get("/activities")
def get_activities():
    return activities


@app.post("/auth/register")
def register(payload: RegisterRequest):
    if payload.email in users:
        raise HTTPException(status_code=409, detail="Email already registered")

    create_user(payload.email, payload.password, payload.role)
    return {
        "message": "Registration successful",
        "user": {"email": payload.email, "role": payload.role}
    }


@app.post("/auth/login")
def login(payload: LoginRequest):
    user = users.get(payload.email)
    if user is None or not verify_password(payload.password, user["salt"], user["password_hash"]):
        raise HTTPException(status_code=401, detail="Invalid email or password")

    token = secrets.token_urlsafe(32)
    sessions[token] = payload.email
    return {
        "message": "Login successful",
        "token": token,
        "user": {"email": user["email"], "role": user["role"]}
    }


@app.get("/auth/session")
def get_session(current_user=Depends(require_authenticated_user)):
    return {"user": {"email": current_user["email"], "role": current_user["role"]}}


@app.post("/auth/logout")
def logout(authorization: Optional[str] = Header(default=None)):
    token = extract_bearer_token(authorization)
    if not token or token not in sessions:
        raise HTTPException(status_code=401, detail="Authentication required")

    sessions.pop(token, None)
    return {"message": "Logout successful"}


@app.post("/activities/{activity_name}/signup")
def signup_for_activity(
    activity_name: str,
    email: Optional[str] = None,
    current_user=Depends(require_authenticated_user),
):
    """Sign up a student for an activity"""
    # Validate activity exists
    if activity_name not in activities:
        raise HTTPException(status_code=404, detail="Activity not found")

    target_email = email or current_user["email"]
    if target_email != current_user["email"] and current_user["role"] != "admin":
        raise HTTPException(status_code=403, detail="Cannot sign up other users")

    # Get the specific activity
    activity = activities[activity_name]

    if len(activity["participants"]) >= activity["max_participants"]:
        raise HTTPException(status_code=400, detail="Activity is full")

    # Validate student is not already signed up
    if target_email in activity["participants"]:
        raise HTTPException(
            status_code=400,
            detail="Student is already signed up"
        )

    # Add student
    activity["participants"].append(target_email)
    return {"message": f"Signed up {target_email} for {activity_name}"}


@app.delete("/activities/{activity_name}/unregister")
def unregister_from_activity(
    activity_name: str,
    email: str,
    current_user=Depends(require_authenticated_user),
):
    """Unregister a student from an activity"""
    # Validate activity exists
    if activity_name not in activities:
        raise HTTPException(status_code=404, detail="Activity not found")

    if email != current_user["email"] and current_user["role"] != "admin":
        raise HTTPException(status_code=403, detail="Cannot unregister other users")

    # Get the specific activity
    activity = activities[activity_name]

    # Validate student is signed up
    if email not in activity["participants"]:
        raise HTTPException(
            status_code=400,
            detail="Student is not signed up for this activity"
        )

    # Remove student
    activity["participants"].remove(email)
    return {"message": f"Unregistered {email} from {activity_name}"}


@app.post("/activities")
def create_activity(
    name: str,
    description: str,
    schedule: str,
    max_participants: int,
    admin_user=Depends(require_admin_user),
):
    """Create a new activity (admin-only)."""
    if name in activities:
        raise HTTPException(status_code=409, detail="Activity already exists")

    if max_participants < 1:
        raise HTTPException(status_code=400, detail="max_participants must be at least 1")

    activities[name] = {
        "description": description,
        "schedule": schedule,
        "max_participants": max_participants,
        "participants": [],
    }
    return {
        "message": f"Created activity {name}",
        "created_by": admin_user["email"],
    }
