from typing import Optional, Dict
from app.core.database import get_dynamodb_table
from botocore.exceptions import ClientError
from app.core.logging_config import get_logger

logger = get_logger(__name__)


class UserService:
    """User profile service for retrieving and managing user records."""

    def get_profile(self, user_id: str) -> Optional[Dict]:
        """Get user profile by user_id.

        Parameters:
        - user_id: unique user id

        Returns:
        - dict of user attributes or None
        """

        logger.info(
            "Fetching user profile",
            extra={
                "event": "service_get_profile_started",
                "user_id": user_id
            }
        )
        
        table = get_dynamodb_table()
        table_key = f"USER#{user_id}"
        
        logger.debug(
            "Querying DynamoDB for user profile",
            extra={
                "event": "dynamodb_get_user_started",
                "user_id": user_id,
                "table_key": table_key
            }
        )
        
        try:
            resp = table.get_item(Key={"claim_id": table_key})
            item = resp.get("Item")
            
            if item:
                logger.info(
                    "User profile retrieved successfully",
                    extra={
                        "event": "service_get_profile_success",
                        "user_id": user_id,
                        "role": item.get("role"),
                        "patient_id": item.get("patient_id")
                    }
                )
            else:
                logger.warning(
                    "User profile not found in DynamoDB",
                    extra={
                        "event": "service_get_profile_not_found",
                        "user_id": user_id,
                        "table_key": table_key
                    }
                )
            
            return item
        except ClientError as e:
            error_code = e.response.get('Error', {}).get('Code', 'Unknown')
            logger.error(
                f"Failed to retrieve user profile from DynamoDB: {error_code}",
                extra={
                    "event": "dynamodb_get_user_failed",
                    "user_id": user_id,
                    "table_key": table_key,
                    "error_code": error_code,
                    "error_message": str(e)
                },
                exc_info=True
            )
            raise
