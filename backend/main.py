
import os
import json
import re


from typing import Optional

from fastapi import (
    FastAPI,
    HTTPException,
    WebSocket,
    WebSocketDisconnect,
    Depends,
    Header,
)
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse

from pydantic import BaseModel, EmailStr

from sqlalchemy import (
    create_engine,
    Column,
    Integer,
    String,
    Boolean,
    DateTime,
    Text,
    ForeignKey,
)
from sqlalchemy.orm import declarative_base, sessionmaker, Session

from passlib.context import CryptContext

import jwt

from openai import OpenAI

from datetime import datetime, timezone

# ============================================================
# CONFIGURATION
# ============================================================

DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "sqlite:///./screenguide.db"
)

JWT_SECRET = os.getenv(
    "JWT_SECRET",
    "change-this-in-production"
)

JWT_ALG = "HS256"


# ============================================================
# DATABASE
# ============================================================

engine = create_engine(
    DATABASE_URL,
    connect_args={
        "check_same_thread": False
    } if DATABASE_URL.startswith("sqlite") else {}
)

SessionLocal = sessionmaker(
    bind=engine,
    autocommit=False,
    autoflush=False
)

Base = declarative_base()


# ============================================================
# PASSWORD HASHING
# ============================================================

# PBKDF2 avoids bcrypt's 72-byte password limitation.
pwd = CryptContext(
    schemes=["pbkdf2_sha256"],
    deprecated="auto"
)

security = HTTPBearer()

def hash_password(password: str) -> str:
    if not password:
        raise HTTPException(
            status_code=400,
            detail="Password cannot be empty"
        )

    return pwd.hash(password)


def verify_password(
    password: str,
    password_hash: str
) -> bool:
    try:
        return pwd.verify(
            password,
            password_hash
        )
    except Exception:
        return False


# ============================================================
# OPENAI
# ============================================================

GROQ_API_KEY = os.getenv("GROQ_API_KEY")
GROQ_TEXT_MODEL = os.getenv("GROQ_TEXT_MODEL", "openai/gpt-oss-20b")
GROQ_VISION_MODEL = os.getenv("GROQ_VISION_MODEL", "qwen/qwen3.6-27b")

client = (
    OpenAI(
        api_key=GROQ_API_KEY,
        base_url="https://api.groq.com/openai/v1"
    )
    if GROQ_API_KEY
    else None
)


# ============================================================
# DATABASE MODELS
# ============================================================

class User(Base):
    __tablename__ = "users"

    id = Column(
        Integer,
        primary_key=True
    )

    email = Column(
        String(255),
        unique=True,
        index=True,
        nullable=False
    )

    password_hash = Column(
        String(255),
        nullable=False
    )

    created_at = Column(
        DateTime,
        default=lambda: datetime.now(timezone.utc)
    )


class Task(Base):
    __tablename__ = "tasks"

    id = Column(
        Integer,
        primary_key=True
    )

    user_id = Column(
        Integer,
        ForeignKey("users.id"),
        nullable=False
    )

    goal = Column(
        Text,
        nullable=False
    )

    steps_json = Column(
        Text,
        nullable=False
    )

    current_step = Column(
        Integer,
        default=0
    )

    completed = Column(
        Boolean,
        default=False
    )

    created_at = Column(
        DateTime,
        default=lambda: datetime.now(timezone.utc)
    )


class SessionRow(Base):
    __tablename__ = "sessions"

    id = Column(
        Integer,
        primary_key=True
    )

    user_id = Column(
        Integer,
        ForeignKey("users.id"),
        nullable=False
    )

    task_id = Column(
        Integer,
        nullable=True
    )

    started_at = Column(
        DateTime,
        default=lambda: datetime.now(timezone.utc)
    )

    ended_at = Column(
        DateTime,
        nullable=True
    )


# Create tables AFTER models are defined.
Base.metadata.create_all(engine)


# ============================================================
# FASTAPI APPLICATION
# ============================================================

app = FastAPI(
    title="ScreenGuide AI Phase 8"
)


# ============================================================
# FRONTEND
# ============================================================

app.mount(
    "/frontend",
    StaticFiles(directory="frontend"),
    name="frontend"
)


@app.get("/")
def home():
    return FileResponse(
        "frontend/index.html"
    )


# ============================================================
# CORS
# ============================================================

app.add_middleware(
    CORSMiddleware,
    allow_origins=os.getenv(
        "CORS_ORIGINS",
        "*"
    ).split(","),
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ============================================================
# REQUEST MODELS
# ============================================================

class AuthIn(BaseModel):
    email: EmailStr
    password: str


class PlanIn(BaseModel):
    goal: str


class AgentIn(BaseModel):
    image: Optional[str] = None
    goal: str
    steps: Optional[list] = None
    current_step: int = 0


# ============================================================
# DATABASE DEPENDENCY
# ============================================================

def db():
    database = SessionLocal()

    try:
        yield database
    finally:
        database.close()


# ============================================================
# JWT FUNCTIONS
# ============================================================

def token_for(user):
    return jwt.encode(
        {
            "sub": str(user.id),
            "email": user.email,
            "exp": datetime.now(timezone.utc)
        },
        JWT_SECRET,
        algorithm=JWT_ALG,
    )


def decode_token(token: str):
    try:
        return jwt.decode(
            token,
            JWT_SECRET,
            algorithms=[JWT_ALG]
        )
    except Exception:
        raise HTTPException(
            status_code=401,
            detail="Invalid or expired token"
        )


def bearer_user(
    authorization: str,
    database: Session
):
    if not authorization:
        raise HTTPException(
            status_code=401,
            detail="Missing Authorization header"
        )

    if not authorization.startswith("Bearer "):
        raise HTTPException(
            status_code=401,
            detail="Invalid Authorization header"
        )

    token = authorization[7:].strip()

    if not token:
        raise HTTPException(
            status_code=401,
            detail="Missing bearer token"
        )

    payload = decode_token(token)

    try:
        user_id = int(payload["sub"])
    except Exception:
        raise HTTPException(
            status_code=401,
            detail="Invalid token"
        )

    user = database.get(
        User,
        user_id
    )

    if not user:
        raise HTTPException(
            status_code=401,
            detail="User not found"
        )

    return user


# ============================================================
# REGISTER
# ============================================================

@app.post("/api/auth/register")
def register(
    x: AuthIn,
    database: Session = Depends(db)
):
    existing_user = (
        database.query(User)
        .filter(User.email == x.email)
        .first()
    )

    if existing_user:
        raise HTTPException(
            status_code=400,
            detail="Email already registered"
        )

    user = User(
        email=x.email,
        password_hash=hash_password(
            x.password
        )
    )

    database.add(user)
    database.commit()
    database.refresh(user)

    return {
        "access_token": token_for(user),
        "user": {
            "id": user.id,
            "email": user.email
        }
    }


# ============================================================
# LOGIN
# ============================================================

@app.post("/api/auth/login")
def login(
    x: AuthIn,
    database: Session = Depends(db)
):
    user = (
        database.query(User)
        .filter(User.email == x.email)
        .first()
    )

    if not user:
        raise HTTPException(
            status_code=401,
            detail="Invalid email or password"
        )

    if not verify_password(
        x.password,
        user.password_hash
    ):
        raise HTTPException(
            status_code=401,
            detail="Invalid email or password"
        )

    return {
        "access_token": token_for(user),
        "user": {
            "id": user.id,
            "email": user.email
        }
    }


# ============================================================
# TASK PLANNER
# ============================================================

@app.post("/api/tasks/plan")
def plan(
    x: PlanIn,
    credentials: HTTPAuthorizationCredentials = Depends(security),
    database: Session = Depends(db)
):
    user = bearer_user(
        f"Bearer {credentials.credentials}",
        database
    )

    steps = []

    if client:
        prompt = f"""
Create a safe, user-driven UI task plan for this goal:

{x.goal}

Return ONLY valid JSON:

{{
    "steps": [
        {{
            "title": "short action"
        }}
    ]
}}

Use 4 to 6 concrete UI steps.

Never include passwords, OTPs, payment secrets,
private keys, or autonomous computer actions.
"""

        try:
            response = client.responses.create(
                model=GROQ_TEXT_MODEL,
                input=prompt
            )

            text = response.output_text.strip()

            match = re.search(
                r"\{.*\}",
                text,
                re.DOTALL
            )

            if match:
                parsed = json.loads(
                    match.group()
                )

                if isinstance(
                    parsed.get("steps"),
                    list
                ):
                    steps = parsed["steps"]

        except Exception:
            steps = []

    # Safe fallback
    if not steps:
        steps = [
            {
                "title":
                "Understand the current page"
            },
            {
                "title":
                "Complete the required action"
            },
            {
                "title":
                "Review the result"
            },
            {
                "title":
                "Finish the task"
            }
        ]

    task = Task(
        user_id=user.id,
        goal=x.goal,
        steps_json=json.dumps(steps),
        current_step=0,
        completed=False
    )

    database.add(task)
    database.commit()
    database.refresh(task)

    return {
        "id": task.id,
        "goal": task.goal,
        "steps": [
            {
                **step,
                "done": False
            }
            for step in steps
        ],
        "current_step": 0,
        "completed": False,
        "created_at":
            task.created_at.isoformat()
    }


# ============================================================
# VISION AGENT
# ============================================================

@app.post("/api/agent")
def agent(
    x: AgentIn,
    credentials: HTTPAuthorizationCredentials = Depends(security),
    database: Session = Depends(db)
):
    bearer_user(f"Bearer {credentials.credentials}", database)

    demo_responses = [
        {"answer": "Look for the YouTube search box at the top of the page.", "completed": False, "point": {"x": 0.50, "y": 0.15, "label": "Search box"}},
        {"answer": "Click the search box and type your Python video search.", "completed": False, "point": {"x": 0.50, "y": 0.15, "label": "Search"}},
        {"answer": "Review the search results and choose a relevant Python video.", "completed": False, "point": {"x": 0.50, "y": 0.45, "label": "Video result"}},
        {"answer": "The task is complete. You can now review the selected video.", "completed": True, "point": None},
    ]

    if not client or not x.image:
        step = max(0, min(x.current_step, len(demo_responses) - 1))
        return {**demo_responses[step], "mode": "demo"}

    system_prompt = """You are ScreenGuide AI, a cautious real-time visual task assistant.
Analyze the screenshot against the user's goal and current step. Give ONE concise next instruction. Never request passwords, OTPs, API keys, private keys, payment card numbers, or other secrets. Do not perform or claim to perform computer actions.
Return ONLY valid JSON: {\"answer\":\"concise next instruction\",\"completed\":false,\"point\":{\"x\":0.5,\"y\":0.5,\"label\":\"short target\"}}. Set completed=true only when the current step is visibly completed. point may be null. Coordinates are normalized 0..1 from the top-left."""

    image_url = x.image if x.image.startswith("data:image/") else "data:image/jpeg;base64," + x.image
    user_text = json.dumps({"goal": x.goal, "current_step": x.current_step, "steps": x.steps or []})

    try:
        response = client.chat.completions.create(
            model=GROQ_VISION_MODEL,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": [
                    {"type": "text", "text": user_text},
                    {"type": "image_url", "image_url": {"url": image_url}}
                ]}
            ],
            temperature=0.1,
            max_completion_tokens=500,
            response_format={"type": "json_object"}
        )
        text = response.choices[0].message.content or "{}"
        try:
            result = json.loads(text)
        except Exception:
            match = re.search(r"\{.*\}", text, re.DOTALL)
            result = json.loads(match.group()) if match else {}
        return {
            "answer": result.get("answer", "Look at the highlighted area and complete the current step."),
            "completed": bool(result.get("completed", False)),
            "point": result.get("point"),
            "mode": "groq"
        }
    except Exception as error:
        step = max(0, min(x.current_step, len(demo_responses) - 1))
        return {**demo_responses[step], "mode": "demo-fallback", "error": str(error)}


# ============================================================
# WEBSOCKET AGENT
# ============================================================

@app.websocket("/ws/agent")
async def ws_agent(
    websocket: WebSocket
):
    await websocket.accept()

    try:
        first_message = json.loads(
            await websocket.receive_text()
        )

        token = first_message.get(
            "token",
            ""
        )

        payload = decode_token(
            token
        )

        user_id = int(
            payload["sub"]
        )

        await websocket.send_json(
            {
                "type": "ready",
                "message":
                    "WebSocket agent connected"
            }
        )

        while True:
            message = json.loads(
                await websocket.receive_text()
            )

            if message.get("type") != "frame":
                continue

            await websocket.send_json(
                {
                    "type": "status",
                    "status": "frame_received",
                    "user_id": user_id
                }
            )

    except WebSocketDisconnect:
        pass

    except Exception:
        try:
            await websocket.close(
                code=1008
            )
        except Exception:
            pass


# ============================================================
# HEALTH CHECK
# ============================================================

@app.get("/api/health")
def health():
    return {
        "status": "ok",
        "time":
            datetime.utcnow().isoformat(),
        "database": "configured",
        "groq": "configured" if client else "missing GROQ_API_KEY",
        "text_model": GROQ_TEXT_MODEL,
        "vision_model": GROQ_VISION_MODEL
    }