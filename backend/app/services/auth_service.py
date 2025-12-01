import time
import uuid
from typing import Optional

import boto3
from botocore.exceptions import ClientError
import jwt
from passlib.context import CryptContext

from app.core.config import settings
from app.core.database import get_dynamodb_table
from app.core.auth import get_jwt_secret
from app.schemas.auth import LoginRequest, LoginResponse, RegisterRequest, RegisterResponse


pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


class AuthService:
    """Authentication service handling registration and login with JWT issuance.

    Uses DynamoDB single-table to store user profiles and hashed passwords, and
    AWS Secrets Manager to retrieve the JWT signing secret.
    """

    def _hash_password(self, password: str) -> str:
        """Hash a plaintext password using bcrypt.

        Parameters:
        - password: plaintext password

        Returns:
        - bcrypt hash string
        """

        return pwd_context.hash(password)

    def _verify_password(self, password: str, hashed: str) -> bool:
        """Verify a plaintext password against a bcrypt hash.

        Parameters:
        - password: plaintext password
        - hashed: stored bcrypt hash

        Returns:
        - True if password matches, else False
        """

        return pwd_context.verify(password, hashed)

    def register(self, req: RegisterRequest) -> RegisterResponse:
        """Register a new user.

        Parameters:
        - req: registration payload including email, password, role, and name

        Returns:
        - RegisterResponse with user_id and optional patient_id
        """

        table = get_dynamodb_table()
        user_id = str(uuid.uuid4())
        patient_id: Optional[str] = None
        if req.role == "patient":
            patient_id = f"PAT-{str(uuid.uuid4())[:8]}"

        item = {
            "claim_id": f"USER#{user_id}",
            "user_id": user_id,
            "email": req.email,
            "password_hash": self._hash_password(req.password),
            "role": req.role,
            "name": req.name,
            "patient_id": patient_id,
            "created_at": int(time.time())
        }
        try:
            table.put_item(Item=item)
        except ClientError as e:
            raise e
        return RegisterResponse(user_id=user_id, patient_id=patient_id)

    def login(self, req: LoginRequest) -> LoginResponse:
        """Authenticate a user and issue a JWT.

        Parameters:
        - req: login payload including email and password

        Returns:
        - LoginResponse containing token, role, user_id, and optional patient_id
        """

        table = get_dynamodb_table()
        try:
            if req.patient_id:
                scan = table.scan(
                    FilterExpression=boto3.dynamodb.conditions.Attr("patient_id").eq(req.patient_id)
                )
            else:
                scan = table.scan(
                    FilterExpression=boto3.dynamodb.conditions.Attr("email").eq(req.email)
                )
        except ClientError as e:
            raise e
        items = scan.get("Items", [])
        user = items[0] if items else None

        if not user:
            # Seed default admin if email matches configured admin
            if req.email == settings.ADMIN_EMAIL:
                user_id = str(uuid.uuid4())
                item = {
                    "claim_id": f"USER#{user_id}",
                    "user_id": user_id,
                    "email": settings.ADMIN_EMAIL,
                    "password_hash": self._hash_password(settings.ADMIN_PASSWORD),
                    "role": "admin",
                    "patient_id": None,
                    "name": "System Admin",
                    "created_at": int(time.time())
                }
                table.put_item(Item=item)
                user = item
            else:
                raise ValueError("Invalid credentials")

        if not self._verify_password(req.password, user.get("password_hash", "")):
            raise ValueError("Invalid credentials")

        secret = get_jwt_secret()
        payload = {
            "sub": user["user_id"],
            "role": user["role"],
            "patient_id": user.get("patient_id"),
            "iat": int(time.time()),
            "exp": int(time.time()) + 60 * 60
        }
        token = jwt.encode(payload, secret, algorithm=settings.JWT_ALGORITHM)

        return LoginResponse(
            token=token,
            role=user["role"],
            user_id=user["user_id"],
            patient_id=user.get("patient_id")
        )
