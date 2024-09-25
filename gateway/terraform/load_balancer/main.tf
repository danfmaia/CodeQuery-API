# Declare variables
variable "subnets" {
  type = list(string)
}

variable "certificate_arn" {
  type = string
}

variable "vpc_id" {
  type = string
}

variable "security_group" {
  type = string
}

variable "ec2_instance_id" {
  type = string
}

# Load Balancer Configuration
resource "aws_lb" "app_lb" {
  name               = "gateway-lb"
  internal           = false
  load_balancer_type = "application"
  security_groups    = [var.security_group]  # Use the passed security group variable
  subnets            = var.subnets
}

resource "aws_lb_target_group" "app_tg" {
  name     = "gateway-tg"
  port     = 8080
  protocol = "HTTP"
  vpc_id   = var.vpc_id

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
  target_id        = var.ec2_instance_id  # Use the passed EC2 instance ID
  port             = 8080
}

output "aws_lb_app_lb_dns_name" {
  value = aws_lb.app_lb.dns_name
}
