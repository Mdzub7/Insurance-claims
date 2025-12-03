import uuid
import datetime
import boto3  # <--- THIS WAS MISSING
from botocore.exceptions import ClientError
from app.core.database import get_dynamodb_table, get_s3_client
from app.core.config import settings
from app.schemas.claim import ClaimCreate, ClaimResponse
from typing import Dict, List, Optional, Tuple
from botocore.client import BaseClient
from fastapi import UploadFile

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

        # 3. Generate S3 Presigned URL for direct PUT (kept for compatibility)
        s3_client = get_s3_client()
        object_key = f"claims/{claim_id}/document.pdf"
        try:
            upload_url = s3_client.generate_presigned_url(
                "put_object",
                Params={"Bucket": settings.S3_BUCKET, "Key": object_key, "ContentType": "application/pdf"},
                ExpiresIn=3600,
            )
        except ClientError as e:
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

    def get_claims_by_user(self, user_id: str) -> List[Dict]:
        """List claims for a user and attach short-lived document view URLs.

        Parameters:
        - user_id: unique user identifier

        Returns:
        - list of claim items with optional 'document_url' when document_key exists
        """
        table = get_dynamodb_table()
        response = table.query(
            IndexName="UserIndex",
            KeyConditionExpression=boto3.dynamodb.conditions.Key("user_id").eq(user_id),
        )
        items = response.get("Items", [])
        # Filter out any log records per single-table convention
        items = [i for i in items if not str(i.get("claim_id", "")).startswith("LOG#")]
        return self._attach_document_urls(items)

    def upload_document(self, claim_id: str, file: UploadFile) -> Dict:
        """Upload a claim document to S3 and update DynamoDB with the object key.

        Parameters:
        - claim_id: claim identifier
        - file: uploaded file (expects PDF)

        Returns:
        - dict with 'claim_id' and 'document_url' for immediate viewing
        """
        object_key = f"claims/{claim_id}/document.pdf"
        s3: BaseClient = get_s3_client()
        try:
            s3.upload_fileobj(file.file, settings.S3_BUCKET, object_key, ExtraArgs={"ContentType": file.content_type or "application/pdf"})
        except ClientError as e:
            raise RuntimeError(str(e))

        table = get_dynamodb_table()
        try:
            table.update_item(
                Key={"claim_id": claim_id},
                UpdateExpression="SET document_key = :k, document_uploaded_at = :t",
                ExpressionAttributeValues={":k": object_key, ":t": datetime.datetime.utcnow().isoformat()},
            )
        except ClientError as e:
            raise RuntimeError(str(e))

        url = s3.generate_presigned_url(
            "get_object",
            Params={"Bucket": settings.S3_BUCKET, "Key": object_key},
            ExpiresIn=900,
        )
        return {"claim_id": claim_id, "document_url": url}

    def confirm_document(self, claim_id: str, object_key: Optional[str] = None) -> Dict:
        """Confirm document upload and persist object key if provided.

        Parameters:
        - claim_id: claim identifier
        - object_key: optional object key to set

        Returns:
        - updated attributes of the claim item
        """
        table = get_dynamodb_table()
        expr = "SET document_confirmed_at = :t"
        values: Dict[str, str] = {":t": datetime.datetime.utcnow().isoformat()}
        if object_key:
            expr += ", document_key = :k"
            values[":k"] = object_key
        try:
            resp = table.update_item(
                Key={"claim_id": claim_id},
                UpdateExpression=expr,
                ExpressionAttributeValues=values,
                ReturnValues="ALL_NEW",
            )
            return resp.get("Attributes", {})
        except ClientError as e:
            raise RuntimeError(str(e))

    def _attach_document_urls(self, items: List[Dict]) -> List[Dict]:
        """Internal: attach presigned get URLs to items with document_key.

        Parameters:
        - items: list of claim records

        Returns:
        - items enriched with 'document_url' when document_key present
        """
        s3 = get_s3_client()
        enriched: List[Dict] = []
        for i in items:
            key = i.get("document_key")
            if key:
                try:
                    i["document_url"] = s3.generate_presigned_url(
                        "get_object",
                        Params={"Bucket": settings.S3_BUCKET, "Key": key},
                        ExpiresIn=900,
                    )
                except ClientError:
                    pass
            enriched.append(i)
        return enriched
