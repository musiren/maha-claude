from pydantic import BaseModel
from typing import Optional


class LoginRequest(BaseModel):
    username: str
    password: str


class LoginResponse(BaseModel):
    token: str


class SessionStartResponse(BaseModel):
    session_id: str


class SessionEndRequest(BaseModel):
    session_id: str


class CommandRequest(BaseModel):
    session_id: str
    command: str


class ApprovalRequest(BaseModel):
    session_id: str
    approval_id: str
    approved: bool


class ErrorResponse(BaseModel):
    code: str
    message: str
