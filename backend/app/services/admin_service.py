from typing import List, Dict, Optional
import boto3
from botocore.exceptions import ClientError
from app.core.database import get_dynamodb_table, get_s3_client
from app.core.config import settings
from app.core.logging_config import get_logger

logger = get_logger(__name__)


class AdminService:
    """Admin operations for users and claims."""

    def list_users(self) -> List[Dict]:
        """List all users."""
        logger.info(
            "Listing all users",
            extra={"event": "service_list_users_started"}
        )
        
        table = get_dynamodb_table()
        
        logger.debug(
            "Scanning DynamoDB for user records",
            extra={
                "event": "dynamodb_scan_users_started",
                "filter": "claim_id begins_with USER#"
            }
        )
        
        try:
            resp = table.scan(FilterExpression=boto3.dynamodb.conditions.Attr("claim_id").begins_with("USER#"))
            users = resp.get("Items", [])
            
            logger.info(
                "Users listed successfully",
                extra={
                    "event": "service_list_users_success",
                    "user_count": len(users)
                }
            )
            
            return users
        except ClientError as e:
            error_code = e.response.get('Error', {}).get('Code', 'Unknown')
            logger.error(
                f"Failed to list users: {error_code}",
                extra={
                    "event": "dynamodb_scan_users_failed",
                    "error_code": error_code,
                    "error_message": str(e)
                },
                exc_info=True
            )
            raise

    def delete_user(self, user_id: str) -> None:
        """Delete a user record."""
        logger.info(
            "Deleting user record",
            extra={
                "event": "service_delete_user_started",
                "target_user_id": user_id
            }
        )
        
        table = get_dynamodb_table()
        table_key = f"USER#{user_id}"
        
        logger.debug(
            "Deleting user from DynamoDB",
            extra={
                "event": "dynamodb_delete_user_started",
                "target_user_id": user_id,
                "table_key": table_key
            }
        )
        
        try:
            table.delete_item(Key={"claim_id": table_key})
            
            logger.info(
                "User deleted successfully",
                extra={
                    "event": "service_delete_user_success",
                    "target_user_id": user_id
                }
            )
        except ClientError as e:
            error_code = e.response.get('Error', {}).get('Code', 'Unknown')
            logger.error(
                f"Failed to delete user: {error_code}",
                extra={
                    "event": "dynamodb_delete_user_failed",
                    "target_user_id": user_id,
                    "error_code": error_code,
                    "error_message": str(e)
                },
                exc_info=True
            )
            raise

    def list_pending_claims(self) -> List[Dict]:
        """List claims with status PENDING."""
        logger.info(
            "Listing pending claims",
            extra={"event": "service_list_pending_started"}
        )
        
        table = get_dynamodb_table()
        
        logger.debug(
            "Scanning DynamoDB for pending claims",
            extra={
                "event": "dynamodb_scan_pending_started",
                "status_filter": "PENDING"
            }
        )
        
        try:
            resp = table.scan(FilterExpression=boto3.dynamodb.conditions.Attr("claim_status").eq("PENDING"))
            claims = resp.get("Items", [])
            
            logger.info(
                "Pending claims listed successfully",
                extra={
                    "event": "service_list_pending_success",
                    "pending_count": len(claims)
                }
            )
            
            return self._attach_document_urls(claims)
        except ClientError as e:
            error_code = e.response.get('Error', {}).get('Code', 'Unknown')
            logger.error(
                f"Failed to list pending claims: {error_code}",
                extra={
                    "event": "dynamodb_scan_pending_failed",
                    "error_code": error_code,
                    "error_message": str(e)
                },
                exc_info=True
            )
            raise

    def list_claims(self, status: Optional[str] = None) -> List[Dict]:
        """List claims, optionally filtered by status."""
        logger.info(
            "Listing claims",
            extra={
                "event": "service_list_claims_started",
                "status_filter": status
            }
        )
        
        table = get_dynamodb_table()
        attr = boto3.dynamodb.conditions.Attr("claim_status")
        
        logger.debug(
            "Scanning DynamoDB for claims",
            extra={
                "event": "dynamodb_scan_claims_started",
                "status_filter": status
            }
        )
        
        try:
            if status:
                resp = table.scan(FilterExpression=attr.eq(status))
            else:
                resp = table.scan(FilterExpression=attr.exists())
            
            claims = resp.get("Items", [])
            
            logger.info(
                "Claims listed successfully",
                extra={
                    "event": "service_list_claims_success",
                    "status_filter": status,
                    "claim_count": len(claims)
                }
            )
            
            return self._attach_document_urls(claims)
        except ClientError as e:
            error_code = e.response.get('Error', {}).get('Code', 'Unknown')
            logger.error(
                f"Failed to list claims: {error_code}",
                extra={
                    "event": "dynamodb_scan_claims_failed",
                    "status_filter": status,
                    "error_code": error_code,
                    "error_message": str(e)
                },
                exc_info=True
            )
            raise

    def list_claims_by_patient(self, patient_id: str) -> List[Dict]:
        """List all claims for a given patient_id."""
        logger.info(
            "Listing claims for patient",
            extra={
                "event": "service_list_patient_claims_started",
                "patient_id": patient_id
            }
        )
        
        table = get_dynamodb_table()
        
        logger.debug(
            "Scanning DynamoDB for patient claims",
            extra={
                "event": "dynamodb_scan_patient_claims_started",
                "patient_id": patient_id
            }
        )
        
        try:
            resp = table.scan(FilterExpression=boto3.dynamodb.conditions.Attr("patient_id").eq(patient_id))
            claims = resp.get("Items", [])
            
            logger.info(
                "Patient claims listed successfully",
                extra={
                    "event": "service_list_patient_claims_success",
                    "patient_id": patient_id,
                    "claim_count": len(claims)
                }
            )
            
            return self._attach_document_urls(claims)
        except ClientError as e:
            error_code = e.response.get('Error', {}).get('Code', 'Unknown')
            logger.error(
                f"Failed to list patient claims: {error_code}",
                extra={
                    "event": "dynamodb_scan_patient_claims_failed",
                    "patient_id": patient_id,
                    "error_code": error_code,
                    "error_message": str(e)
                },
                exc_info=True
            )
            raise

    def update_claim_status(self, claim_id: str, status: str) -> Dict:
        """Update claim status."""
        logger.info(
            "Updating claim status",
            extra={
                "event": "service_update_status_started",
                "claim_id": claim_id,
                "new_status": status
            }
        )
        
        table = get_dynamodb_table()
        
        logger.debug(
            "Updating claim status in DynamoDB",
            extra={
                "event": "dynamodb_update_status_started",
                "claim_id": claim_id,
                "new_status": status
            }
        )
        
        try:
            resp = table.update_item(
                Key={"claim_id": claim_id},
                UpdateExpression="SET claim_status = :s",
                ExpressionAttributeValues={":s": status},
                ReturnValues="ALL_NEW"
            )
            attributes = resp.get("Attributes", {})
            
            logger.info(
                "Claim status updated successfully",
                extra={
                    "event": "service_update_status_success",
                    "claim_id": claim_id,
                    "new_status": status,
                    "previous_status": attributes.get("claim_status")
                }
            )
            
            return attributes
        except ClientError as e:
            error_code = e.response.get('Error', {}).get('Code', 'Unknown')
            logger.error(
                f"Failed to update claim status: {error_code}",
                extra={
                    "event": "dynamodb_update_status_failed",
                    "claim_id": claim_id,
                    "new_status": status,
                    "error_code": error_code,
                    "error_message": str(e)
                },
                exc_info=True
            )
            raise RuntimeError(str(e))

    def _attach_document_urls(self, items: List[Dict]) -> List[Dict]:
        """Attach presigned view URLs for items with document_key."""
        logger.debug(
            "Attaching document URLs to items",
            extra={
                "event": "admin_attach_urls_started",
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
                except Exception as e:
                    logger.warning(
                        "Failed to generate document URL",
                        extra={
                            "event": "document_url_generation_failed",
                            "claim_id": i.get("claim_id"),
                            "document_key": key,
                            "error_type": type(e).__name__,
                            "error_message": str(e)
                        }
                    )
                    pass
            enriched.append(i)
        
        logger.debug(
            "Document URLs attached",
            extra={
                "event": "admin_attach_urls_completed",
                "item_count": len(items),
                "urls_attached": urls_attached
            }
        )
        
        return enriched
