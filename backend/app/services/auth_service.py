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
from app.core.logging_config import get_logger

logger = get_logger(__name__)

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

        logger.debug(
            "Hashing password with bcrypt",
            extra={"event": "password_hash_started"}
        )
        return pwd_context.hash(password)

    def _verify_password(self, password: str, hashed: str) -> bool:
        """Verify a plaintext password against a bcrypt hash.

        Parameters:
        - password: plaintext password
        - hashed: stored bcrypt hash

        Returns:
        - True if password matches, else False
        """

        logger.debug(
            "Verifying password against stored hash",
            extra={"event": "password_verify_started"}
        )
        result = pwd_context.verify(password, hashed)
        
        if result:
            logger.debug(
                "Password verification successful",
                extra={"event": "password_verify_success"}
            )
        else:
            logger.debug(
                "Password verification failed - hash mismatch",
                extra={"event": "password_verify_failed", "reason": "hash_mismatch"}
            )
        return result

    def register(self, req: RegisterRequest) -> RegisterResponse:
        """Register a new user.

        Parameters:
        - req: registration payload including email, password, role, and name

        Returns:
        - RegisterResponse with user_id and optional patient_id
        """

        logger.info(
            "Starting user registration process",
            extra={
                "event": "service_register_started",
                "email": req.email,
                "role": req.role,
                "name": req.name
            }
        )

        table = get_dynamodb_table()
        user_id = str(uuid.uuid4())
        patient_id: Optional[str] = None
        if req.role == "patient":
            patient_id = f"PAT-{str(uuid.uuid4())[:8]}"
            logger.debug(
                "Generated patient ID for patient role",
                extra={
                    "event": "patient_id_generated",
                    "patient_id": patient_id,
                    "user_id": user_id
                }
            )

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
        
        logger.debug(
            "Storing user record in DynamoDB",
            extra={
                "event": "dynamodb_put_user_started",
                "user_id": user_id,
                "table_key": f"USER#{user_id}"
            }
        )
        
        try:
            table.put_item(Item=item)
            logger.info(
                "User record stored successfully in DynamoDB",
                extra={
                    "event": "dynamodb_put_user_success",
                    "user_id": user_id,
                    "email": req.email,
                    "role": req.role,
                    "patient_id": patient_id
                }
            )
        except ClientError as e:
            error_code = e.response.get('Error', {}).get('Code', 'Unknown')
            logger.error(
                f"Failed to store user record in DynamoDB: {error_code}",
                extra={
                    "event": "dynamodb_put_user_failed",
                    "user_id": user_id,
                    "email": req.email,
                    "error_code": error_code,
                    "error_message": str(e)
                },
                exc_info=True
            )
            raise e
        return RegisterResponse(user_id=user_id, patient_id=patient_id)

    def login(self, req: LoginRequest) -> LoginResponse:
        """Authenticate a user and issue a JWT.

        Parameters:
        - req: login payload including email and password

        Returns:
        - LoginResponse containing token, role, user_id, and optional patient_id
        """

        login_method = "patient_id" if req.patient_id else "email"
        login_identifier = req.patient_id if req.patient_id else req.email
        
        logger.info(
            "Starting user authentication process",
            extra={
                "event": "service_login_started",
                "login_method": login_method,
                "identifier": login_identifier
            }
        )

        table = get_dynamodb_table()
        
        logger.debug(
            "Querying DynamoDB for user record",
            extra={
                "event": "dynamodb_scan_user_started",
                "login_method": login_method,
                "identifier": login_identifier
            }
        )
        
        try:
            if req.patient_id:
                scan = table.scan(
                    FilterExpression=boto3.dynamodb.conditions.Attr("patient_id").eq(req.patient_id)
                )
            else:
                scan = table.scan(
                    FilterExpression=boto3.dynamodb.conditions.Attr("email").eq(req.email)
                )
            
            logger.debug(
                "DynamoDB scan completed",
                extra={
                    "event": "dynamodb_scan_user_completed",
                    "login_method": login_method,
                    "items_found": len(scan.get("Items", []))
                }
            )
        except ClientError as e:
            error_code = e.response.get('Error', {}).get('Code', 'Unknown')
            logger.error(
                f"DynamoDB scan failed: {error_code}",
                extra={
                    "event": "dynamodb_scan_user_failed",
                    "login_method": login_method,
                    "identifier": login_identifier,
                    "error_code": error_code,
                    "error_message": str(e)
                },
                exc_info=True
            )
            raise e
        
        items = scan.get("Items", [])
        user = items[0] if items else None

        if not user:
            logger.debug(
                "No user found with provided credentials",
                extra={
                    "event": "user_lookup_no_match",
                    "login_method": login_method,
                    "identifier": login_identifier
                }
            )
            
            # Seed default admin if email matches configured admin
            if req.email == settings.ADMIN_EMAIL:
                logger.info(
                    "Seeding default admin user",
                    extra={
                        "event": "admin_seed_started",
                        "email": settings.ADMIN_EMAIL
                    }
                )
                
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
                
                try:
                    table.put_item(Item=item)
                    logger.info(
                        "Default admin user seeded successfully",
                        extra={
                            "event": "admin_seed_success",
                            "user_id": user_id,
                            "email": settings.ADMIN_EMAIL
                        }
                    )
                except ClientError as e:
                    logger.error(
                        "Failed to seed admin user",
                        extra={
                            "event": "admin_seed_failed",
                            "error_message": str(e)
                        },
                        exc_info=True
                    )
                    raise e
                user = item
            else:
                logger.warning(
                    "Login failed - no user found with provided credentials",
                    extra={
                        "event": "login_failed_no_user",
                        "login_method": login_method,
                        "identifier": login_identifier
                    }
                )
                raise ValueError("Invalid credentials")

        # Verify password
        logger.debug(
            "Verifying password for user",
            extra={
                "event": "password_verification_started",
                "user_id": user.get("user_id"),
                "role": user.get("role")
            }
        )
        
        if not self._verify_password(req.password, user.get("password_hash", "")):
            logger.warning(
                "Login failed - password verification failed",
                extra={
                    "event": "login_failed_wrong_password",
                    "login_method": login_method,
                    "identifier": login_identifier,
                    "user_id": user.get("user_id")
                }
            )
            raise ValueError("Invalid credentials")

        logger.debug(
            "Password verified, generating JWT token",
            extra={
                "event": "jwt_generation_started",
                "user_id": user["user_id"],
                "role": user["role"]
            }
        )

        secret = get_jwt_secret()
        payload = {
            "sub": user["user_id"],
            "role": user["role"],
            "patient_id": user.get("patient_id"),
            "iat": int(time.time()),
            "exp": int(time.time()) + 60 * 60
        }
        token = jwt.encode(payload, secret, algorithm=settings.JWT_ALGORITHM)

        logger.info(
            "JWT token generated successfully - login complete",
            extra={
                "event": "login_success",
                "user_id": user["user_id"],
                "role": user["role"],
                "patient_id": user.get("patient_id"),
                "token_expiry_seconds": 3600
            }
        )

        return LoginResponse(
            token=token,
            role=user["role"],
            user_id=user["user_id"],
            patient_id=user.get("patient_id")
        )
