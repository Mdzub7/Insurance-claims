from pydantic import BaseModel, EmailStr, Field
from typing import Optional


class LoginRequest(BaseModel):
    """Request body for login.

    Parameters:
    - email: User email address
    - password: Plaintext password to be verified
    """

    email: Optional[EmailStr] = None
    patient_id: Optional[str] = None
    password: str = Field(min_length=8)


class LoginResponse(BaseModel):
    """Response body for successful login.

    Returns:
    - token: JWT bearer token
    - role: User role ('patient' | 'admin')
    - user_id: Unique user identifier
    - patient_id: Patient identifier when role is 'patient'
    """

    token: str
    role: str
    user_id: str
    patient_id: Optional[str] = None


class RegisterRequest(BaseModel):
    """Request body for user registration.

    Parameters:
    - email: User email address
    - password: Plaintext password to be hashed
    - role: 'patient' or 'admin'
    - name: Full name of the user
    """

    email: EmailStr
    password: str = Field(min_length=8)
    role: str
    name: str


class RegisterResponse(BaseModel):
    """Response body for successful registration.

    Returns:
    - user_id: Unique user identifier
    - patient_id: Generated patient id when role is 'patient'
    """

    user_id: str
    patient_id: Optional[str] = None
