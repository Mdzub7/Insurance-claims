from typing import Optional, Dict
from app.core.database import get_dynamodb_table


class UserService:
    """User profile service for retrieving and managing user records."""

    def get_profile(self, user_id: str) -> Optional[Dict]:
        """Get user profile by user_id.

        Parameters:
        - user_id: unique user id

        Returns:
        - dict of user attributes or None
        """

        table = get_dynamodb_table()
        resp = table.get_item(Key={"claim_id": f"USER#{user_id}"})
        return resp.get("Item")
