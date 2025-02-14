data "aws_caller_identity" "current" {}

# S3 Bucket for storing API keys and ngrok URL
resource "aws_s3_bucket" "codequery_gateway_bucket" {
  bucket = "codequery-gateway-storage"

  tags = {
    Name = "codequery-gateway-bucket"
  }
}

# Configure server-side encryption for the bucket
resource "aws_s3_bucket_server_side_encryption_configuration" "bucket_encryption" {
  bucket = aws_s3_bucket.codequery_gateway_bucket.id

  rule {
    apply_server_side_encryption_by_default {
      kms_master_key_id = aws_kms_key.api_key_encryption_key.arn
      sse_algorithm     = "aws:kms"
    }
  }
}

# Block public access to the bucket
resource "aws_s3_bucket_public_access_block" "bucket_public_access_block" {
  bucket = aws_s3_bucket.codequery_gateway_bucket.id

  block_public_acls       = true
  block_public_policy     = true
  ignore_public_acls      = true
  restrict_public_buckets = true
}

# Create an AWS KMS Key for encrypting API keys in S3
resource "aws_kms_key" "api_key_encryption_key" {
  description             = "KMS key for encrypting API keys in S3"
  deletion_window_in_days = 10
  enable_key_rotation     = true

  tags = {
    Name = "api_key_encryption_key"
  }
}

# Allow IAM role to use the KMS key
resource "aws_kms_key_policy" "allow_ec2_access" {
  key_id = aws_kms_key.api_key_encryption_key.id

  policy = jsonencode({
    Version = "2012-10-17"
    Id      = "key-default-1"
    Statement = [
      {
        Sid    = "Enable IAM User Permissions"
        Effect = "Allow"
        Principal = {
          AWS = "arn:aws:iam::${data.aws_caller_identity.current.account_id}:root"
        }
        Action   = "kms:*"
        Resource = "*"
      },
      {
        Sid    = "Allow Gateway Instance Role to use the key"
        Effect = "Allow"
        Principal = {
          AWS = aws_iam_role.gateway_instance_role.arn
        }
        Action = [
          "kms:Encrypt",
          "kms:Decrypt",
          "kms:ReEncrypt*",
          "kms:GenerateDataKey*",
          "kms:DescribeKey"
        ]
        Resource = "*"
      }
    ]
  })
}

# Enable versioning using a separate resource
resource "aws_s3_bucket_versioning" "codequery_gateway_versioning" {
  bucket = aws_s3_bucket.codequery_gateway_bucket.id

  versioning_configuration {
    status = "Enabled"
  }
}

# IAM Role for EC2 instance to access S3 bucket
resource "aws_iam_role" "gateway_instance_role" {
  name = "gateway_instance_role"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Action = "sts:AssumeRole"
        Effect = "Allow"
        Principal = {
          Service = "ec2.amazonaws.com"
        }
      }
    ]
  })
}

# IAM Policy for EC2 instance to interact with the S3 bucket
resource "aws_iam_policy" "gateway_s3_policy" {
  name        = "gateway_s3_policy"
  description = "Allows EC2 to access S3 for managing encrypted API keys"

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Action = [
          "s3:GetObject",
          "s3:PutObject",
          "s3:ListBucket"
        ]
        Resource = [
          aws_s3_bucket.codequery_gateway_bucket.arn,
          "${aws_s3_bucket.codequery_gateway_bucket.arn}/*"
        ]
      },
      {
        Effect = "Allow"
        Action = [
          "kms:Encrypt",
          "kms:Decrypt",
          "kms:GenerateDataKey"
        ]
        Resource = aws_kms_key.api_key_encryption_key.arn
      }
    ]
  })
}

# Attach the policy to the role
resource "aws_iam_role_policy_attachment" "gateway_role_policy_attachment" {
  role       = aws_iam_role.gateway_instance_role.name
  policy_arn = aws_iam_policy.gateway_s3_policy.arn
}

# Create IAM Instance Profile for EC2 to assume the role
resource "aws_iam_instance_profile" "gateway_instance_profile" {
  name = "gateway_instance_profile"
  role = aws_iam_role.gateway_instance_role.name
}

# Upload the .env file to S3
resource "aws_s3_object" "env_file" {
  count  = fileexists("${path.root}/../.env") ? 1 : 0
  bucket = aws_s3_bucket.codequery_gateway_bucket.id
  key    = ".env"
  source = "${path.root}/../.env"
  
  server_side_encryption = "aws:kms"
  kms_key_id            = aws_kms_key.api_key_encryption_key.arn
}

# Upload the gateway.py file to S3
resource "aws_s3_object" "gateway_py_file" {
  count  = fileexists("${path.root}/../gateway.py") ? 1 : 0
  bucket = aws_s3_bucket.codequery_gateway_bucket.id
  key    = "gateway.py"
  source = "${path.root}/../gateway.py"
  
  server_side_encryption = "aws:kms"
  kms_key_id            = aws_kms_key.api_key_encryption_key.arn
}

# Upload the requirements.txt file to S3
resource "aws_s3_object" "requirements_file" {
  count  = fileexists("${path.root}/../requirements.txt") ? 1 : 0
  bucket = aws_s3_bucket.codequery_gateway_bucket.id
  key    = "requirements.txt"
  source = "${path.root}/../requirements.txt"
  
  server_side_encryption = "aws:kms"
  kms_key_id            = aws_kms_key.api_key_encryption_key.arn
}

# Initialize API keys in S3 (empty placeholder)
resource "aws_s3_object" "api_keys_file" {
  bucket  = aws_s3_bucket.codequery_gateway_bucket.id
  key     = "api_keys.json"
  content = "{}"  # Empty JSON object as placeholder
  server_side_encryption = "aws:kms"
  kms_key_id = aws_kms_key.api_key_encryption_key.arn
}

# Outputs
output "s3_bucket_name" {
  value = aws_s3_bucket.codequery_gateway_bucket.bucket
}

output "iam_instance_profile_name" {
  value = aws_iam_instance_profile.gateway_instance_profile.name
}
