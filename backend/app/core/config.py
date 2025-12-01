from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    PROJECT_NAME: str = "Cloud-Native Insurance System"
    AWS_REGION: str = "eu-west-2"
    # These names must match your Terraform Outputs!
    DYNAMODB_TABLE: str = "intl-capstone-team2-claims-dev" 
    S3_BUCKET: str = "intl-euro-capstone-team2-dev" # Update this with your actual bucket name
    JWT_SECRET_NAME: str = "jwt_secret"
    JWT_ALGORITHM: str = "HS256"
    ADMIN_EMAIL: str = "admin@healthcare.com"
    ADMIN_PASSWORD: str = "SecureAdmin@123"

    class Config:
        case_sensitive = True

settings = Settings()
