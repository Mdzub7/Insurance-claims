import boto3
from app.core.config import settings
from app.core.logging_config import get_logger

logger = get_logger(__name__)

# We create the clients once and reuse them (Singleton pattern equivalent)
def get_dynamodb_table():
    logger.debug(
        "Getting DynamoDB table resource",
        extra={
            "event": "dynamodb_table_access",
            "table_name": settings.DYNAMODB_TABLE,
            "region": settings.AWS_REGION
        }
    )
    dynamodb = boto3.resource("dynamodb", region_name=settings.AWS_REGION)
    return dynamodb.Table(settings.DYNAMODB_TABLE)

def get_s3_client():
    logger.debug(
        "Getting S3 client",
        extra={
            "event": "s3_client_access",
            "bucket": settings.S3_BUCKET,
            "region": settings.AWS_REGION
        }
    )
    return boto3.client("s3", region_name=settings.AWS_REGION)
