from fastapi import APIRouter
from pydantic import BaseModel, EmailStr
from backend.controllers.auth_controller import register_user, authenticate_user

router = APIRouter(prefix="/api/auth", tags=["Authentication"])


class SignupRequest(BaseModel):
    name: str
    email: EmailStr
    password: str


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


@router.post("/signup")
async def signup_endpoint(request: SignupRequest):
    """Creates a new user profile."""
    return register_user(
        name=request.name,
        email=request.email,
        password=request.password
    )


@router.post("/login")
async def login_endpoint(request: LoginRequest):
    """Authenticates existing user."""
    return authenticate_user(
        email=request.email,
        password=request.password
    )
