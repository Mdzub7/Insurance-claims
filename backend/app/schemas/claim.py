from pydantic import BaseModel
from typing import Optional
from datetime import datetime

# Base Schema: Shared properties
class ClaimBase(BaseModel):
    amount: float
    description: str
    policy_number: str

# Create Schema: What the user sends to US (Input)
class ClaimCreate(ClaimBase):
    pass

# Response Schema: What WE send back (Output)
# We add fields like 'claim_id' and 'status' which the user cannot set themselves.
class ClaimResponse(ClaimBase):
    claim_id: str
    claim_status: str
    created_at: str
    s3_upload_url: Optional[str] = None # Presigned URL
    user_id: str

    class Config:
        from_attributes = True
