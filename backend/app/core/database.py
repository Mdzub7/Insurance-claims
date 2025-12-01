import boto3
from app.core.config import settings

# We create the clients once and reuse them (Singleton pattern equivalent)
def get_dynamodb_table():
    dynamodb = boto3.resource("dynamodb", region_name=settings.AWS_REGION)
    return dynamodb.Table(settings.DYNAMODB_TABLE)

def get_s3_client():
    return boto3.client("s3", region_name=settings.AWS_REGION)
