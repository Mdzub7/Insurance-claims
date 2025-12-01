# --- DYNAMODB TABLE ---
resource "aws_dynamodb_table" "claims_table" {
  name         = "${var.project_name}-claims-${var.environment}"
  billing_mode = "PAY_PER_REQUEST" # Save money (Serverless model)
  hash_key     = "claim_id"

  attribute {
    name = "claim_id"
    type = "S" # String
  }
  
  # Global Secondary Index for querying by User
  attribute {
    name = "user_id"
    type = "S"
  }

  global_secondary_index {
    name            = "UserIndex"
    hash_key        = "user_id"
    projection_type = "ALL"
  }

  tags = {
    Name        = "${var.project_name}-dynamodb"
    Environment = var.environment
  }
}

variable "existing_s3_bucket_name" {
  description = "The name of the pre-existing S3 bucket provided by Cigna"
  type        = string
  default = "intl-euro-capstone-team2" #<--- Optional: set a default
}

# --- S3 BUCKET FOR DOCUMENTS ---
#resource "aws_s3_bucket" "claims_docs" {
#  bucket = "${var.project_name}-caps-${var.environment}" # Must be globally unique
  
  # Force destroy allows deleting bucket even if files exist (Good for Dev, Bad for Prod)
#  force_destroy = true 
#  tags = {
#    Name        = "${var.project_name}-s3"
#    Environment = var.environment
#  }
#}

 # Enable Versioning (Compliance Requirement)
# resource "aws_s3_bucket_versioning" "docs_versioning" {
#  bucket = aws_s3_bucket.claims_docs.id
#  versioning_configuration {
#    status = "Enabled"
#  }
#}

# --- SQS QUEUE ---
resource "aws_sqs_queue" "claims_queue" {
  name                      = "${var.project_name}-queue-${var.environment}"
  delay_seconds             = 0
  max_message_size          = 262144 # 256 KB
  message_retention_seconds = 86400  # 1 day
  receive_wait_time_seconds = 10     # Long polling (cheaper)
}

output "sqs_queue_url" {
  value = aws_sqs_queue.claims_queue.url
}

# --- SECRETS MANAGER ---
resource "aws_secretsmanager_secret" "jwt_secret" {
  name = "${var.project_name}-jwt-secret-${var.environment}-v1"
  description = "Secret key for signing JWT Authentication tokens"
}

# We create a random string to put inside the secret automatically
resource "aws_secretsmanager_secret_version" "jwt_secret_val" {
  secret_id     = aws_secretsmanager_secret.jwt_secret.id
  secret_string = "SUPER_SECRET_KEY_CHANGE_ME_IN_PROD_12345"
}

# 1. The Trust Policy (Who can assume this role? Lambda service)
data "aws_iam_policy_document" "lambda_assume_role" {
  statement {
    effect = "Allow"
    principals {
      type        = "Service"
      identifiers = ["lambda.amazonaws.com"]
    }
    actions = ["sts:AssumeRole"]
  }
}

resource "aws_iam_role" "lambda_processor_role" {
  name               = "${var.project_name}-lambda-role"
  assume_role_policy = data.aws_iam_policy_document.lambda_assume_role.json
}

# 2. The Permissions Policy (What can this role DO?)
resource "aws_iam_policy" "lambda_policy" {
  name        = "${var.project_name}-lambda-policy"
  description = "Allow Lambda to read S3 and write to SQS"

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        # Allow Logging (Crucial for debugging!)
        Action   = ["logs:CreateLogGroup", "logs:CreateLogStream", "logs:PutLogEvents"]
        Effect   = "Allow"
        Resource = "arn:aws:logs:*:*:*"
      },
      {
        # Allow Reading from S3 Bucket
        Action   = ["s3:GetObject"]
        Effect   = "Allow"
        Resource = "arn:aws:s3:::${var.existing_s3_bucket_name}/*"
      },
      {
        # Allow Sending messages to SQS
        Action   = ["sqs:SendMessage"]
        Effect   = "Allow"
        Resource = aws_sqs_queue.claims_queue.arn
      }
    ]
  })
}

# 3. Attach Policy to Role
resource "aws_iam_role_policy_attachment" "attach_lambda_policy" {
  role       = aws_iam_role.lambda_processor_role.name
  policy_arn = aws_iam_policy.lambda_policy.arn
}

# --- LAMBDA PACKAGING ---
# This zips your python file automatically
data "archive_file" "lambda_zip" {
  type        = "zip"
  source_file = "${path.module}/../lambda/processor.py"
  output_path = "${path.module}/../lambda/processor.zip"
}


# --- LAMBDA FUNCTION ---
resource "aws_lambda_function" "processor" {
  filename      = data.archive_file.lambda_zip.output_path
  function_name = "${var.project_name}-processor-${var.environment}"
  role          = aws_iam_role.lambda_processor_role.arn
  handler       = "processor.lambda_handler" # filename.function_name
  runtime       = "python3.9"
  source_code_hash = data.archive_file.lambda_zip.output_base64sha256

  environment {
    variables = {
      SQS_QUEUE_URL = aws_sqs_queue.claims_queue.url
    }
  }
}

# --- S3 TRIGGER CONFIGURATION ---
# 1. Give S3 permission to call Lambda
resource "aws_lambda_permission" "allow_s3" {
  statement_id  = "AllowExecutionFromS3"
  action        = "lambda:InvokeFunction"
  function_name = aws_lambda_function.processor.function_name
  principal     = "s3.amazonaws.com"
  source_arn    = "arn:aws:s3:::${var.existing_s3_bucket_name}"
}

# 2. Set the trigger on the Bucket
resource "aws_s3_bucket_notification" "bucket_notification" {
  bucket = var.existing_s3_bucket_name

  lambda_function {
    lambda_function_arn = aws_lambda_function.processor.arn
    events              = ["s3:ObjectCreated:*"] # Trigger on PUT or POST
    filter_prefix       = "claims/"              # Only trigger for files in claims/ folder
  }
  
  depends_on = [aws_lambda_permission.allow_s3]
}

