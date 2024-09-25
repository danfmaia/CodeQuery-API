# Declare variables
variable "cert_validation_name" {
  type        = string
}

variable "cert_validation_record" {
  type        = string
}

variable "certificate_arn" {
  type        = string
}

# Route53 Zone
resource "aws_route53_zone" "codequery_zone" {
  name = "codequery.dev"
}

# SSL Certificate Validation Record in Route53
resource "aws_route53_record" "cert_validation" {
  name    = var.cert_validation_name
  type    = "CNAME"
  zone_id = aws_route53_zone.codequery_zone.zone_id
  ttl     = 300

  records = [var.cert_validation_record]
}

# SSL Certificate Validation
resource "aws_acm_certificate_validation" "cert_validation" {
  certificate_arn         = var.certificate_arn
  validation_record_fqdns = [aws_route53_record.cert_validation.fqdn]
}
