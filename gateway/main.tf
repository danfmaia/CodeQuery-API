# Define variables
variable "aws_region" {
  description = "AWS region to deploy resources in"
}
variable "ami_id" {
  description = "AMI ID for EC2 instance"
}
variable "certificate_arn" {
  description = "Certificate ARN for SSL"
}
variable "key_name" {
  description = "Key pair for EC2"
}
variable "vpc_id" {
  description = "VPC ID for the instance"
}
variable "subnets" {
  description = "Subnets for the load balancer"
  type        = list(string)
}
variable "ssh_cidr_block" {
  description = "CIDR block for SSH access"
}
variable "cert_validation_name" {
  description = "DNS name for certificate validation"
}
variable "cert_validation_record" {
  description = "Certificate validation CNAME record"
}


provider "aws" {
  region = var.aws_region
}

# Define the EC2 instance
resource "aws_instance" "codequery_gateway" {
  ami           = var.ami_id
  instance_type = "t2.micro"
  key_name      = var.key_name

  disable_api_termination = true  # Enable termination protection

  # Automatically install FastAPI via user data
  user_data = <<-EOF
            #!/bin/bash
            sudo yum update -y
            sudo yum install -y python3
            sudo yum install -y python3-pip
          
            # Check if virtualenv exists; if not, create it
            if [ ! -d "/home/ec2-user/codequery-gateway/venv" ]; then
                python3 -m venv /home/ec2-user/codequery-gateway/venv
            fi
            
            source /home/ec2-user/codequery-gateway/venv/bin/activate
            
            # Install dependencies from requirements.txt inside the virtual environment
            if [ -f /home/ec2-user/codequery-gateway/requirements.txt ]; then
                pip install -r /home/ec2-user/codequery-gateway/requirements.txt
            else
                echo "requirements.txt not found"
                exit 1
            fi

            # Create systemd service for FastAPI
            echo "
            [Unit]
            Description=FastAPI app
            After=network.target

            [Service]
            ExecStart=/bin/bash -c 'source /home/ec2-user/codequery-gateway/venv/bin/activate && exec uvicorn app:app --host 0.0.0.0 --port 8080'
            Restart=always

            [Install]
            WantedBy=multi-user.target
            " > /etc/systemd/system/fastapi.service

            # Reload systemd, enable and start FastAPI
            sudo systemctl daemon-reload
            sudo systemctl enable fastapi
            sudo systemctl start fastapi
            EOF

  # Set up Security Group
  vpc_security_group_ids = [aws_security_group.allow_ssh_http_https.id]

  # Define the instance tags
  tags = {
    Name = "CodeQuery-Gateway"
  }
}

# Security Group to allow HTTP, HTTPS, and SSH access
resource "aws_security_group" "allow_ssh_http_https" {
  name        = "allow_ssh_http_https"
  description = "Allow HTTP, HTTPS, and SSH traffic"

  # Allow HTTPS access on port 443
  ingress {
    description = "Allow HTTPS"
    from_port   = 443
    to_port     = 443
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
  }

  # Allow HTTP access on port 8080 (for internal communication between the ALB and EC2)
  ingress {
    description = "Allow HTTP"
    from_port   = 8080
    to_port     = 8080
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
  }

  # Allow SSH access from a specific IP
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

resource "aws_lb" "app_lb" {
  name               = "codequery-gateway-lb"
  internal           = false
  load_balancer_type = "application"
  security_groups    = [aws_security_group.allow_ssh_http_https.id]
  subnets            = var.subnets  # Load from environment
}

resource "aws_lb_target_group" "app_tg" {
  name     = "codequery-gateway-tg"
  port     = 8080
  protocol = "HTTP"
  vpc_id   = var.vpc_id  # Load from environment

  health_check {
    path                = "/"
    interval            = 30
    timeout             = 5
    healthy_threshold   = 2
    unhealthy_threshold = 2
    matcher             = "200"
  }
}

resource "aws_lb_listener" "https_listener" {
  load_balancer_arn = aws_lb.app_lb.arn
  port              = "443"
  protocol          = "HTTPS"
  ssl_policy        = "ELBSecurityPolicy-2016-08"
  certificate_arn   = var.certificate_arn

  default_action {
    type             = "forward"
    target_group_arn = aws_lb_target_group.app_tg.arn
  }
}

resource "aws_lb_listener" "http_redirect_listener" {
  load_balancer_arn = aws_lb.app_lb.arn
  port              = "80"
  protocol          = "HTTP"

  default_action {
    type = "redirect"

    redirect {
      port        = "443"
      protocol    = "HTTPS"
      status_code = "HTTP_301"
    }
  }
}

resource "aws_lb_target_group_attachment" "app_lb_attachment" {
  target_group_arn = aws_lb_target_group.app_tg.arn
  target_id        = aws_instance.codequery_gateway.id
  port             = 8080
}

resource "aws_route53_zone" "codequery_zone" {
  name = "codequery.dev"
}

resource "aws_route53_record" "cert_validation" {
  name    = var.cert_validation_name
  type    = "CNAME"
  zone_id = aws_route53_zone.codequery_zone.zone_id
  ttl     = 300

  records = [var.cert_validation_record]
}

resource "aws_acm_certificate_validation" "cert_validation" {
  certificate_arn         = var.certificate_arn
  validation_record_fqdns = [aws_route53_record.cert_validation.fqdn]
}
