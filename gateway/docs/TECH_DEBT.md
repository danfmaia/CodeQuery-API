# Technical Debt

## S3 and Security Improvements

### High Priority

1. ~~**S3 Bucket Security**~~ ✅
   - ~~Add server-side encryption for all S3 objects using existing KMS key~~
   - ~~Configure bucket-level encryption~~
   - ~~Add public access blocking~~
   - ~~Enforce SSL/TLS for S3 access~~

### Medium Priority

1. **IAM and KMS**
   - Review and tighten KMS key policy
   - Consider using AWS Secrets Manager for API key storage
   - Implement principle of least privilege for IAM roles
   - Add automated key rotation for KMS keys

### Low Priority

1. **Infrastructure**

   - Add tags for better resource management
   - Implement backup strategy for S3 objects
   - Add monitoring and alerting for security events
   - Add CloudWatch metrics for API key usage

2. **Documentation**
   - Add architecture diagrams
   - Document disaster recovery procedures
   - Create runbooks for common operations

## Development Tools

### Medium Priority

1. **Build and Deployment**

   - Add Makefile to streamline common operations:
     - `make init`: Setup development environment
     - `make deploy`: Deploy to EC2
     - `make test`: Run tests locally and on EC2
     - `make logs`: View and manage service logs
     - `make api-keys`: Manage API keys
     - `make clean`: Cleanup temporary files and logs
   - Add environment validation in Makefile targets
   - Add colored output for better visibility
   - Add help target with command descriptions

2. **Development Experience**
   - Add pre-commit hooks for code formatting
   - Add automated version management
   - Add development/staging/production environment configs

## API Management

### High Priority

1. **API Key Management**
   - Add endpoint to purge all data associated with a specific API key
     - Remove key from `api_keys.json`
     - Remove key from `ngrok_urls.json`
     - Add authentication to ensure only authorized users can purge keys
     - Add logging for audit trail
     - Consider soft delete option for data recovery
   - Add validation to ensure Gateway admin key cannot be purged
