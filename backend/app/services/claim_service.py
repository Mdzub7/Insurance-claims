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
from app.core.logging_config import get_logger

logger = get_logger(__name__)


class ClaimService:
    def create_claim(self, claim_data: ClaimCreate, current_user: dict) -> ClaimResponse:
        claim_id = str(uuid.uuid4())
        timestamp = datetime.datetime.utcnow().isoformat()
        user_id = current_user.get("sub")
        patient_id = current_user.get("patient_id")
        
        logger.info(
            "Creating new insurance claim",
            extra={
                "event": "service_create_claim_started",
                "claim_id": claim_id,
                "user_id": user_id,
                "patient_id": patient_id,
                "amount": str(claim_data.amount),
                "policy_number": claim_data.policy_number
            }
        )
        
        # 1. Prepare the Item for DynamoDB
        item = {
            "claim_id": claim_id,
            "user_id": user_id,
            "patient_id": patient_id,
            "claim_status": "PENDING",
            "amount": str(claim_data.amount), 
            "description": claim_data.description,
            "policy_number": claim_data.policy_number,
            "created_at": timestamp
        }

        # 2. Save to DynamoDB
        logger.debug(
            "Storing claim record in DynamoDB",
            extra={
                "event": "dynamodb_put_claim_started",
                "claim_id": claim_id,
                "user_id": user_id
            }
        )
        
        table = get_dynamodb_table()
        try:
            table.put_item(Item=item)
            logger.info(
                "Claim record stored successfully in DynamoDB",
                extra={
                    "event": "dynamodb_put_claim_success",
                    "claim_id": claim_id,
                    "user_id": user_id,
                    "status": "PENDING"
                }
            )
        except ClientError as e:
            error_code = e.response.get('Error', {}).get('Code', 'Unknown')
            logger.error(
                f"Failed to store claim in DynamoDB: {error_code}",
                extra={
                    "event": "dynamodb_put_claim_failed",
                    "claim_id": claim_id,
                    "user_id": user_id,
                    "error_code": error_code,
                    "error_message": str(e)
                },
                exc_info=True
            )
            raise

        # 3. Generate S3 Presigned URL for direct PUT (kept for compatibility)
        s3_client = get_s3_client()
        object_key = f"claims/{claim_id}/document.pdf"
        
        logger.debug(
            "Generating S3 presigned URL for document upload",
            extra={
                "event": "s3_presigned_url_started",
                "claim_id": claim_id,
                "bucket": settings.S3_BUCKET,
                "object_key": object_key
            }
        )
        
        try:
            upload_url = s3_client.generate_presigned_url(
                "put_object",
                Params={"Bucket": settings.S3_BUCKET, "Key": object_key, "ContentType": "application/pdf"},
                ExpiresIn=3600,
            )
            logger.debug(
                "S3 presigned URL generated successfully",
                extra={
                    "event": "s3_presigned_url_success",
                    "claim_id": claim_id,
                    "object_key": object_key,
                    "expires_in": 3600
                }
            )
        except ClientError as e:
            error_code = e.response.get('Error', {}).get('Code', 'Unknown')
            logger.warning(
                f"Failed to generate S3 presigned URL: {error_code}",
                extra={
                    "event": "s3_presigned_url_failed",
                    "claim_id": claim_id,
                    "bucket": settings.S3_BUCKET,
                    "error_code": error_code,
                    "error_message": str(e)
                }
            )
            upload_url = None

        logger.info(
            "Claim creation completed successfully",
            extra={
                "event": "service_create_claim_success",
                "claim_id": claim_id,
                "user_id": user_id,
                "patient_id": patient_id,
                "has_upload_url": upload_url is not None
            }
        )

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
        logger.info(
            "Fetching claims for user",
            extra={
                "event": "service_get_claims_started",
                "user_id": user_id
            }
        )
        
        table = get_dynamodb_table()
        
        logger.debug(
            "Querying DynamoDB UserIndex for claims",
            extra={
                "event": "dynamodb_query_claims_started",
                "user_id": user_id,
                "index": "UserIndex"
            }
        )
        
        try:
            response = table.query(
                IndexName="UserIndex",
                KeyConditionExpression=boto3.dynamodb.conditions.Key("user_id").eq(user_id),
            )
            items = response.get("Items", [])
            
            logger.debug(
                "DynamoDB query completed",
                extra={
                    "event": "dynamodb_query_claims_completed",
                    "user_id": user_id,
                    "items_found": len(items)
                }
            )
        except ClientError as e:
            error_code = e.response.get('Error', {}).get('Code', 'Unknown')
            logger.error(
                f"DynamoDB query failed: {error_code}",
                extra={
                    "event": "dynamodb_query_claims_failed",
                    "user_id": user_id,
                    "error_code": error_code,
                    "error_message": str(e)
                },
                exc_info=True
            )
            raise
        
        # Filter out any log records per single-table convention
        original_count = len(items)
        items = [i for i in items if not str(i.get("claim_id", "")).startswith("LOG#")]
        filtered_count = original_count - len(items)
        
        if filtered_count > 0:
            logger.debug(
                "Filtered out log records from results",
                extra={
                    "event": "claims_filtered",
                    "user_id": user_id,
                    "original_count": original_count,
                    "filtered_count": filtered_count,
                    "final_count": len(items)
                }
            )
        
        result = self._attach_document_urls(items)
        
        logger.info(
            "Claims retrieved successfully",
            extra={
                "event": "service_get_claims_success",
                "user_id": user_id,
                "claim_count": len(result)
            }
        )
        
        return result

    def upload_document(self, claim_id: str, file: UploadFile) -> Dict:
        """Upload a claim document to S3 and update DynamoDB with the object key.

        Parameters:
        - claim_id: claim identifier
        - file: uploaded file (expects PDF)

        Returns:
        - dict with 'claim_id' and 'document_url' for immediate viewing
        """
        object_key = f"claims/{claim_id}/document.pdf"
        
        logger.info(
            "Uploading document to S3",
            extra={
                "event": "service_upload_document_started",
                "claim_id": claim_id,
                "filename": file.filename,
                "content_type": file.content_type,
                "bucket": settings.S3_BUCKET,
                "object_key": object_key
            }
        )
        
        s3: BaseClient = get_s3_client()
        try:
            s3.upload_fileobj(file.file, settings.S3_BUCKET, object_key, ExtraArgs={"ContentType": file.content_type or "application/pdf"})
            logger.info(
                "Document uploaded to S3 successfully",
                extra={
                    "event": "s3_upload_success",
                    "claim_id": claim_id,
                    "bucket": settings.S3_BUCKET,
                    "object_key": object_key
                }
            )
        except ClientError as e:
            error_code = e.response.get('Error', {}).get('Code', 'Unknown')
            logger.error(
                f"S3 upload failed: {error_code}",
                extra={
                    "event": "s3_upload_failed",
                    "claim_id": claim_id,
                    "bucket": settings.S3_BUCKET,
                    "object_key": object_key,
                    "error_code": error_code,
                    "error_message": str(e)
                },
                exc_info=True
            )
            raise RuntimeError(str(e))

        logger.debug(
            "Updating claim record with document key",
            extra={
                "event": "dynamodb_update_document_key_started",
                "claim_id": claim_id,
                "object_key": object_key
            }
        )
        
        table = get_dynamodb_table()
        try:
            table.update_item(
                Key={"claim_id": claim_id},
                UpdateExpression="SET document_key = :k, document_uploaded_at = :t",
                ExpressionAttributeValues={":k": object_key, ":t": datetime.datetime.utcnow().isoformat()},
            )
            logger.info(
                "Claim record updated with document key",
                extra={
                    "event": "dynamodb_update_document_key_success",
                    "claim_id": claim_id,
                    "object_key": object_key
                }
            )
        except ClientError as e:
            error_code = e.response.get('Error', {}).get('Code', 'Unknown')
            logger.error(
                f"DynamoDB update failed: {error_code}",
                extra={
                    "event": "dynamodb_update_document_key_failed",
                    "claim_id": claim_id,
                    "error_code": error_code,
                    "error_message": str(e)
                },
                exc_info=True
            )
            raise RuntimeError(str(e))

        logger.debug(
            "Generating presigned URL for document viewing",
            extra={
                "event": "s3_presigned_view_url_started",
                "claim_id": claim_id,
                "object_key": object_key
            }
        )
        
        url = s3.generate_presigned_url(
            "get_object",
            Params={"Bucket": settings.S3_BUCKET, "Key": object_key},
            ExpiresIn=900,
        )
        
        logger.info(
            "Document upload completed successfully",
            extra={
                "event": "service_upload_document_success",
                "claim_id": claim_id,
                "object_key": object_key
            }
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
        logger.info(
            "Confirming document upload",
            extra={
                "event": "service_confirm_document_started",
                "claim_id": claim_id,
                "has_object_key": object_key is not None
            }
        )
        
        table = get_dynamodb_table()
        expr = "SET document_confirmed_at = :t"
        values: Dict[str, str] = {":t": datetime.datetime.utcnow().isoformat()}
        if object_key:
            expr += ", document_key = :k"
            values[":k"] = object_key
            logger.debug(
                "Including object key in confirmation update",
                extra={
                    "event": "confirm_with_object_key",
                    "claim_id": claim_id,
                    "object_key": object_key
                }
            )
        
        try:
            resp = table.update_item(
                Key={"claim_id": claim_id},
                UpdateExpression=expr,
                ExpressionAttributeValues=values,
                ReturnValues="ALL_NEW",
            )
            attributes = resp.get("Attributes", {})
            
            logger.info(
                "Document confirmation completed successfully",
                extra={
                    "event": "service_confirm_document_success",
                    "claim_id": claim_id,
                    "confirmed_at": values[":t"]
                }
            )
            
            return attributes
        except ClientError as e:
            error_code = e.response.get('Error', {}).get('Code', 'Unknown')
            logger.error(
                f"Document confirmation failed: {error_code}",
                extra={
                    "event": "service_confirm_document_failed",
                    "claim_id": claim_id,
                    "error_code": error_code,
                    "error_message": str(e)
                },
                exc_info=True
            )
            raise RuntimeError(str(e))

    def _attach_document_urls(self, items: List[Dict]) -> List[Dict]:
        """Internal: attach presigned get URLs to items with document_key.

        Parameters:
        - items: list of claim records

        Returns:
        - items enriched with 'document_url' when document_key present
        """
        logger.debug(
            "Attaching document URLs to claims",
            extra={
                "event": "attach_document_urls_started",
                "item_count": len(items)
            }
        )
        
        s3 = get_s3_client()
        enriched: List[Dict] = []
        urls_attached = 0
        
        for i in items:
            key = i.get("document_key")
            if key:
                try:
                    i["document_url"] = s3.generate_presigned_url(
                        "get_object",
                        Params={"Bucket": settings.S3_BUCKET, "Key": key},
                        ExpiresIn=900,
                    )
                    urls_attached += 1
                except ClientError as e:
                    logger.warning(
                        "Failed to generate document URL for claim",
                        extra={
                            "event": "document_url_generation_failed",
                            "claim_id": i.get("claim_id"),
                            "document_key": key,
                            "error_message": str(e)
                        }
                    )
                    pass
            enriched.append(i)
        
        logger.debug(
            "Document URLs attached",
            extra={
                "event": "attach_document_urls_completed",
                "item_count": len(items),
                "urls_attached": urls_attached
            }
        )
        
        return enriched
