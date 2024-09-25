# Declare variables
variable "aws_region" {
  description = "AWS region to deploy resources in"
  type        = string
}
variable "ami_id" {
  description = "AMI ID for EC2 instance"
  type        = string
}
variable "certificate_arn" {
  description = "Certificate ARN for SSL"
  type        = string
}
variable "key_name" {
  description = "Key pair for EC2"
  type        = string
}
variable "vpc_id" {
  description = "VPC ID for the instance"
  type        = string
}
variable "subnets" {
  description = "Subnets for the load balancer"
  type        = list(string)
}
variable "ssh_cidr_block" {
  description = "CIDR block for SSH access"
  type        = string
}
variable "cert_validation_name" {
  description = "DNS name for certificate validation"
  type        = string
}
variable "cert_validation_record" {
  description = "Certificate validation CNAME record"
  type        = string
}
variable "key_path" {
  description = "Path to the SSH private key file"
  type        = string
}
variable "s3_bucket_name" {
  type = string
  default = "default-bucket"
}
variable "iam_instance_profile_name" {
  type = string
  default = "default-profile-name"
}


# Initialize the providers and backend for Terraform
terraform {
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 4.0"
    }
  }
  backend "local" {
    path = "terraform.tfstate"
  }
}

provider "aws" {
  region = var.aws_region
}

module "s3" {
  source = "./s3"
}

module "ec2" {
  source          = "./ec2"
  ami_id          = var.ami_id
  key_name        = var.key_name
  vpc_id          = var.vpc_id
  ssh_cidr_block  = var.ssh_cidr_block
  key_path        = var.key_path
  s3_bucket_name            = module.s3.s3_bucket_name
  iam_instance_profile_name = module.s3.iam_instance_profile_name
}

module "load_balancer" {
  source          = "./load_balancer"
  subnets         = var.subnets
  certificate_arn = var.certificate_arn
  vpc_id          = var.vpc_id
  security_group  = module.ec2.aws_security_group_allow_ssh_http_https_id
  ec2_instance_id = module.ec2.aws_instance_codequery_gateway_id
}

module "route53" {
  source                 = "./route53"
  cert_validation_name   = var.cert_validation_name
  cert_validation_record = var.cert_validation_record
  certificate_arn        = var.certificate_arn
}

# Outputs
output "instance_id" {
  value = module.ec2.aws_instance_codequery_gateway_id
}

output "s3_bucket" {
  value = module.s3.s3_bucket_name
}

output "load_balancer_dns" {
  value = module.load_balancer.aws_lb_app_lb_dns_name
}
