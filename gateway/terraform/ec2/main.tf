# Declare variables
variable "ami_id" {
  type = string
}
variable "key_name" {
  type = string
}
variable "vpc_id" {
  type = string
}
variable "ssh_cidr_block" {
  type = string
}
variable "key_path" {
  type        = string
}
variable "s3_bucket_name" {
  type = string
}
variable "iam_instance_profile_name" {
  type = string
}


# EC2 instance configuration and associated security groups
resource "aws_instance" "codequery_gateway" {
  ami           = var.ami_id
  instance_type = "t2.micro"
  key_name      = var.key_name
  iam_instance_profile = var.iam_instance_profile_name  # Attach the IAM role for S3 access

  lifecycle {
    create_before_destroy = true
  }

  disable_api_termination = true  # Enable termination protection

  # Automatically install FastAPI via user data
  user_data = <<-EOF
            #!/bin/bash
            sudo yum update -y
            sudo yum install -y python3
            sudo yum install -y python3-pip
            sudo yum install -y aws-cli

            mkdir -p /home/ec2-user/gateway

            # Download files from S3
            aws s3 cp s3://${var.s3_bucket_name}/.env /home/ec2-user/gateway/.env
            aws s3 cp s3://${var.s3_bucket_name}/gateway.py /home/ec2-user/gateway/gateway.py
            aws s3 cp s3://${var.s3_bucket_name}/requirements.txt /home/ec2-user/gateway/requirements.txt

            # Check if virtualenv exists; if not, create it
            if [ ! -d "/home/ec2-user/gateway/venv" ]; then
                python3 -m venv /home/ec2-user/gateway/venv
            fi

            source /home/ec2-user/gateway/venv/bin/activate

            # Install dependencies from requirements.txt inside the virtual environment
            pip install -r /home/ec2-user/gateway/requirements.txt

            # Create systemd service for FastAPI
            echo "
            [Unit]
            Description=FastAPI app
            After=network.target

            [Service]
            WorkingDirectory=/home/ec2-user/gateway
            ExecStart=/bin/bash -c 'source /home/ec2-user/gateway/venv/bin/activate && exec uvicorn gateway:app --host 0.0.0.0 --port 8080'
            Restart=always

            [Install]
            WantedBy=multi-user.target
            " > /etc/systemd/system/fastapi.service

            sudo systemctl daemon-reload
            sudo systemctl enable fastapi
            sudo systemctl start fastapi
            EOF

  vpc_security_group_ids = [aws_security_group.allow_ssh_http_https.id]

  tags = {
    Name = "gateway"
  }
}



# Save the user_data output for debugging purposes
resource "local_file" "user_data_output" {
  filename = "${path.root}/user_data_output.sh"
  content  = templatefile("${path.root}/user_data_template.sh", {})
}

# Output user_data for inspection
output "user_data" {
  value = aws_instance.codequery_gateway.user_data
}

# Security Group to allow HTTP, HTTPS, and SSH access
resource "aws_security_group" "allow_ssh_http_https" {
  name        = "allow_ssh_http_https_${var.key_name}"
  description = "Allow HTTP, HTTPS, and SSH traffic"
  vpc_id      = var.vpc_id

  ingress {
    description = "Allow HTTPS"
    from_port   = 443
    to_port     = 443
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
  }

  ingress {
    description = "Allow HTTP"
    from_port   = 8080
    to_port     = 8080
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
  }

  ingress {
    description = "Allow SSH from specific IP"
    from_port   = 22
    to_port     = 22
    protocol    = "tcp"
    cidr_blocks = [var.ssh_cidr_block]
  }

  egress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }
}

output "aws_instance_codequery_gateway_id" {
  value = aws_instance.codequery_gateway.id
}

output "aws_security_group_allow_ssh_http_https_id" {
  value = aws_security_group.allow_ssh_http_https.id
}
