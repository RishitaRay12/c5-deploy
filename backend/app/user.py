from datetime import datetime, timedelta, timezone, UTC
import json
from typing import Optional
from jose import JWTError, jwt
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from app.config import settings
from pwdlib import PasswordHash
from pwdlib.hashers.bcrypt import BcryptHasher
from sql_data import get_conn
from psycopg.types.json import Jsonb

password_hash = PasswordHash((BcryptHasher(),))

def hash_password(password: str) -> str:
    return password_hash.hash(password)

def verify_password(plain_password: str, hashed_password: str) -> bool:
    return password_hash.verify(plain_password, hashed_password)


def _json_parameter(value):
    if settings.NEON_DB_URI and settings.DB_FILE == "retail_compliance.db":
        return Jsonb(value)
    return json.dumps(value) if value is not None else None
# Secret key for JWT signing (Keep this secret in environment variables in production)


# pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="users/login")


# Password Hashing & Verification
# def hash_password(password: str) -> str:
#     return pwd_context.hash(password)

# def verify_password(plain_password: str, hashed_password: str) -> bool:
#     return pwd_context.verify(plain_password, hashed_password)

# Token Generation
def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    to_encode = data.copy()
    expire = datetime.now(UTC) + (expires_delta or timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES))
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)

# Dependency to Protect Routes
def get_current_user(token: str = Depends(oauth2_scheme)):
    try:
        payload = jwt.decode(
            token,
            settings.SECRET_KEY,
            algorithms=[settings.ALGORITHM],
        )

        username = payload.get("sub")

        if username is None:
            raise HTTPException(
                status_code=401,
                detail="Invalid authentication credentials",
            )

    except JWTError:
        raise HTTPException(
            status_code=401,
            detail="Invalid authentication credentials",
        )

    with get_conn() as conn:
        cursor = conn.cursor()

        cursor.execute(
            "SELECT * FROM users WHERE username = %s",
            (username,),
        )

        user = cursor.fetchone()

    if user is None:
        raise HTTPException(
            status_code=401,
            detail="User not found",
        )

    return dict(user)

def save_chat_message(
    username: str,
    thread_id: str,
    role: str,
    message: str,
    sources: list[dict] | None = None,
    token_usage: dict | None = None,
) -> None:
    """
    Save one chatbot message.

    role should normally be:
        user
        assistant
    """

    with get_conn() as conn:
        conn.execute(
            """
            INSERT INTO chat_messages (
                username,
                thread_id,
                role,
                message,
                sources,
                token_usage
            )
            VALUES (%s, %s, %s, %s, %s, %s)
            """,
            (
                username,
                thread_id,
                role,
                message,
                _json_parameter(sources or []),
                _json_parameter(token_usage),
            ),
        )


def get_chat_history(
    username: str,
    thread_id: str,
    limit: int = 20,
) -> list[dict]:
    """
    Get the most recent chatbot messages.

    Messages are returned from oldest to newest.
    """

    with get_conn() as conn:
        rows = conn.execute(
            """
            SELECT
                id,
                role,
                message,
                sources,
                token_usage,
                created_at
            FROM (
                SELECT
                    id,
                    role,
                    message,
                    sources,
                    token_usage,
                    created_at
                FROM chat_messages
                WHERE username = %s
                    AND thread_id = %s
                ORDER BY id DESC
                LIMIT %s
            ) AS recent_messages
            ORDER BY id ASC
            """,
            (
                username,
                thread_id,
                limit,
            ),
        ).fetchall()

    messages = []
    for row in rows:
        try:
            sources = row["sources"]
            if isinstance(sources, str):
                sources = json.loads(sources or "[]")
        except (TypeError, json.JSONDecodeError):
            sources = []
        try:
            token_usage = row["token_usage"]
            if isinstance(token_usage, str):
                token_usage = json.loads(token_usage) if token_usage else None
        except (TypeError, json.JSONDecodeError):
            token_usage = None

        messages.append({
            "id": row["id"],
            "role": row["role"],
            "message": row["message"],
            "sources": sources,
            "token_usage": token_usage,
            "created_at": row["created_at"],
        })
    return messages


def get_chat_thread_ids(username: str) -> set[str]:
    """Return thread IDs that have messages owned by the user."""
    with get_conn() as conn:
        rows = conn.execute(
            "SELECT DISTINCT thread_id FROM chat_messages WHERE username = %s",
            (username,),
        ).fetchall()
    return {row["thread_id"] for row in rows}


def delete_chat_thread(username: str, thread_id: str) -> int:
    """Delete all application chat messages for a user's thread."""
    with get_conn() as conn:
        cursor = conn.execute(
            "DELETE FROM chat_messages WHERE username = %s AND thread_id = %s",
            (username, thread_id),
        )
        return cursor.rowcount
