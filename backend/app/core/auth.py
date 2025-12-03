import boto3
from botocore.exceptions import ClientError
from functools import lru_cache
from app.core.config import settings
from app.core.logging_config import get_logger

logger = get_logger(__name__)


@lru_cache(maxsize=1)
def get_jwt_secret() -> str:
    """Retrieve JWT secret string from AWS Secrets Manager and cache it.

    Returns:
    - Secret string used to sign/verify JWT tokens
    """

    logger.info(
        "Retrieving JWT secret from AWS Secrets Manager",
        extra={
            "event": "jwt_secret_retrieval_started",
            "secret_name": settings.JWT_SECRET_NAME,
            "region": settings.AWS_REGION
        }
    )
    
    client = boto3.client("secretsmanager", region_name=settings.AWS_REGION)
    try:
        resp = client.get_secret_value(SecretId=settings.JWT_SECRET_NAME)
        secret = resp.get("SecretString")
        if not secret:
            logger.error(
                "JWT secret retrieved but is empty",
                extra={
                    "event": "jwt_secret_empty",
                    "secret_name": settings.JWT_SECRET_NAME
                }
            )
            raise ValueError("Empty JWT secret")
        
        logger.info(
            "JWT secret successfully retrieved and cached",
            extra={
                "event": "jwt_secret_retrieval_success",
                "secret_name": settings.JWT_SECRET_NAME
            }
        )
        return secret
    except ClientError as e:
        error_code = e.response.get('Error', {}).get('Code', 'Unknown')
        error_message = e.response.get('Error', {}).get('Message', str(e))
        
        logger.error(
            f"Failed to retrieve JWT secret from Secrets Manager: {error_code}",
            extra={
                "event": "jwt_secret_retrieval_failed",
                "secret_name": settings.JWT_SECRET_NAME,
                "error_code": error_code,
                "error_message": error_message,
                "region": settings.AWS_REGION
            },
            exc_info=True
        )
        raise RuntimeError(f"Failed to retrieve JWT secret: {e}")
