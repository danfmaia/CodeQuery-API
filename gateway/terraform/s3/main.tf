# S3 Bucket for storing API keys and ngrok URL
resource "aws_s3_bucket" "codequery_gateway_bucket" {
  bucket = "codequery-gateway-storage"

  tags = {
    Name = "codequery-gateway-bucket"
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
  description = "Allows EC2 to access S3 bucket for storing API keys and ngrok URL"

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
  bucket = aws_s3_bucket.codequery_gateway_bucket.id
  key    = ".env"
  source = "${path.root}/../.env"  # Path to the local .env file
}

# Upload the gateway.py file to S3
resource "aws_s3_object" "gateway_py_file" {
  bucket = aws_s3_bucket.codequery_gateway_bucket.id
  key    = "gateway.py"
  source = "${path.root}/../gateway.py"  # Path to the local gateway.py file
}

# Upload the requirements.txt file to S3
resource "aws_s3_object" "requirements_file" {
  bucket = aws_s3_bucket.codequery_gateway_bucket.id
  key    = "requirements.txt"
  source = "${path.root}/../requirements.txt"  # Path to the local requirements.txt file
}

# Outputs
output "s3_bucket_name" {
  value = aws_s3_bucket.codequery_gateway_bucket.bucket
}

output "iam_instance_profile_name" {
  value = aws_iam_instance_profile.gateway_instance_profile.name
}
