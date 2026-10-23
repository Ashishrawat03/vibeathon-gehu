"""Registration and login endpoints backed by the local SQLite database."""

from __future__ import annotations

import re
import sqlite3
import uuid
from datetime import datetime, timezone

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field, field_validator

from app.core.security import create_token, hash_password, verify_password
from app.db import sqlite as db

router = APIRouter(prefix="/auth", tags=["Authentication"])


class SignupRequest(BaseModel):
    name: str = Field(min_length=1, max_length=100)
    email: str = Field(min_length=3, max_length=254)
    password: str = Field(min_length=8, max_length=128)

    @field_validator("name")
    @classmethod
    def validate_name(cls, value: str) -> str:
        value = value.strip()
        if not value:
            raise ValueError("Name cannot be empty")
        return value

    @field_validator("email")
    @classmethod
    def normalize_email(cls, value: str) -> str:
        value = value.strip().lower()
        if not re.fullmatch(r"[^@\s]+@[^@\s]+\.[^@\s]+", value):
            raise ValueError("Enter a valid email address")
        return value


class LoginRequest(BaseModel):
    email: str = Field(min_length=3, max_length=254)
    password: str = Field(min_length=1, max_length=128)

    @field_validator("email")
    @classmethod
    def normalize_email(cls, value: str) -> str:
        return value.strip().lower()


def _public_user(user: dict) -> dict[str, str]:
    return {"id": user["id"], "name": user["name"], "email": user["email"]}


@router.post("/signup", status_code=201)
def signup(req: SignupRequest) -> dict:
    user = {
        "id": str(uuid.uuid4()),
        "name": req.name,
        "email": req.email,
        "password_hash": hash_password(req.password),
        "created_at": datetime.now(timezone.utc).isoformat(),
    }
    try:
        with db.get_conn() as conn:
            conn.execute(
                "INSERT INTO users (id, name, email, password_hash, created_at) VALUES (?, ?, ?, ?, ?)",
                (user["id"], user["name"], user["email"], user["password_hash"], user["created_at"]),
            )
    except sqlite3.IntegrityError as exc:
        raise HTTPException(status_code=409, detail="An account with this email already exists") from exc

    return {"access_token": create_token(user), "token_type": "bearer", "user": _public_user(user)}


@router.post("/login")
def login(req: LoginRequest) -> dict:
    with db.get_conn() as conn:
        row = conn.execute("SELECT * FROM users WHERE email = ?", (req.email,)).fetchone()
    user = db.row_to_dict(row)
    if not user or not verify_password(req.password, user["password_hash"]):
        raise HTTPException(status_code=401, detail="Email or password is incorrect")

    return {"access_token": create_token(user), "token_type": "bearer", "user": _public_user(user)}
