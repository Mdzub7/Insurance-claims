from typing import List, Dict, Optional
import boto3
from botocore.exceptions import ClientError
from app.core.database import get_dynamodb_table


class AdminService:
    """Admin operations for users and claims."""

    def list_users(self) -> List[Dict]:
        """List all users."""
        table = get_dynamodb_table()
        resp = table.scan(FilterExpression=boto3.dynamodb.conditions.Attr("claim_id").begins_with("USER#"))
        return resp.get("Items", [])

    def delete_user(self, user_id: str) -> None:
        """Delete a user record."""
        table = get_dynamodb_table()
        table.delete_item(Key={"claim_id": f"USER#{user_id}"})

    def list_pending_claims(self) -> List[Dict]:
        """List claims with status PENDING."""
        table = get_dynamodb_table()
        resp = table.scan(FilterExpression=boto3.dynamodb.conditions.Attr("claim_status").eq("PENDING"))
        return resp.get("Items", [])

    def list_claims(self, status: Optional[str] = None) -> List[Dict]:
        """List claims, optionally filtered by status."""
        table = get_dynamodb_table()
        attr = boto3.dynamodb.conditions.Attr("claim_status")
        if status:
            resp = table.scan(FilterExpression=attr.eq(status))
        else:
            resp = table.scan(FilterExpression=attr.exists())
        return resp.get("Items", [])

    def list_claims_by_patient(self, patient_id: str) -> List[Dict]:
        """List all claims for a given patient_id."""
        table = get_dynamodb_table()
        resp = table.scan(FilterExpression=boto3.dynamodb.conditions.Attr("patient_id").eq(patient_id))
        return resp.get("Items", [])

    def update_claim_status(self, claim_id: str, status: str) -> Dict:
        """Update claim status."""
        table = get_dynamodb_table()
        try:
            resp = table.update_item(
                Key={"claim_id": claim_id},
                UpdateExpression="SET claim_status = :s",
                ExpressionAttributeValues={":s": status},
                ReturnValues="ALL_NEW"
            )
            return resp.get("Attributes", {})
        except ClientError as e:
            raise RuntimeError(str(e))
