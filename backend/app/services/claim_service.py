import uuid
import datetime
import boto3  # <--- THIS WAS MISSING
from botocore.exceptions import ClientError
from app.core.database import get_dynamodb_table, get_s3_client
from app.core.config import settings
from app.schemas.claim import ClaimCreate, ClaimResponse

class ClaimService:
    def create_claim(self, claim_data: ClaimCreate, current_user: dict) -> ClaimResponse:
        claim_id = str(uuid.uuid4())
        timestamp = datetime.datetime.utcnow().isoformat()
        
        # 1. Prepare the Item for DynamoDB
        item = {
            "claim_id": claim_id,
            "user_id": current_user.get("sub"),
            "patient_id": current_user.get("patient_id"),
            "claim_status": "PENDING",
            "amount": str(claim_data.amount), 
            "description": claim_data.description,
            "policy_number": claim_data.policy_number,
            "created_at": timestamp
        }

        # 2. Save to DynamoDB
        table = get_dynamodb_table()
        table.put_item(Item=item)

        # 3. Generate S3 Presigned URL
        s3_client = get_s3_client()
        object_key = f"claims/{claim_id}/document.pdf"
        
        try:
            upload_url = s3_client.generate_presigned_url(
                'put_object',
                Params={'Bucket': settings.S3_BUCKET, 'Key': object_key},
                ExpiresIn=3600
            )
        except ClientError as e:
            print(f"Error generating presigned URL: {e}")
            upload_url = None

        # 4. Return the response object
        return ClaimResponse(
            user_id=item["user_id"],
            amount=claim_data.amount,
            description=claim_data.description,
            policy_number=claim_data.policy_number,
            claim_id=claim_id,
            claim_status="PENDING",
            created_at=timestamp,
            s3_upload_url=upload_url
        )

    def get_claims_by_user(self, user_id: str):
        table = get_dynamodb_table()
        # Query the GSI (Global Secondary Index)
        response = table.query(
            IndexName="UserIndex",
            KeyConditionExpression=boto3.dynamodb.conditions.Key('user_id').eq(user_id)
        )
        return response.get('Items', [])
