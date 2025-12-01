import boto3
from botocore.exceptions import ClientError
from functools import lru_cache
from app.core.config import settings


@lru_cache(maxsize=1)
def get_jwt_secret() -> str:
    """Retrieve JWT secret string from AWS Secrets Manager and cache it.

    Returns:
    - Secret string used to sign/verify JWT tokens
    """

    client = boto3.client("secretsmanager", region_name=settings.AWS_REGION)
    try:
        resp = client.get_secret_value(SecretId=settings.JWT_SECRET_NAME)
        secret = resp.get("SecretString")
        if not secret:
            raise ValueError("Empty JWT secret")
        return secret
    except ClientError as e:
        raise RuntimeError(f"Failed to retrieve JWT secret: {e}")
