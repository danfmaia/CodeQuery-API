# Core Testing Guide

Tests can be run both locally and in Docker. The recommended workflow is:

1. Run local unit tests after making changes to Core's code
2. Once local tests pass, run them in Docker to ensure they work in the containerized environment

## Local Testing

### Environment Setup

Before running tests locally, make sure to set up and activate the virtual environment:

```bash
# Create virtual environment (if not already created)
python3 -m venv venv

# Activate virtual environment
source venv/bin/activate  # On Linux/macOS
# or
.\venv\Scripts\activate  # On Windows

# Install dependencies
pip install -r core/requirements.txt
```

### Running Local Tests

Always run tests from the project root directory:

```bash
# Run all tests
python3 -m pytest core/tests -v

# Run specific test file
python3 -m pytest core/tests/test_file_service.py -v
```

## Docker Testing

Docker testing provides a consistent environment and doesn't require local Python setup.

### Prerequisites

- Docker installed and running
- Make utility installed

### Running Docker Tests

```bash
# Build the Docker image
make build

# Run tests in Docker
make test
```

## Important Notes

1. **Test Location**: Always run tests from the project root directory, regardless of the method used.

2. **File Paths**: Always include `core/` prefix in file paths:

   ```python
   # Correct
   "core/src/app.py"

   # Wrong
   "src/app.py"
   ```

3. **Ignore Files**: The `.agentignore` and `.gitignore` files must be in the project root.

## Troubleshooting

### Local Test Issues

- Ensure virtual environment is activated
- Verify you're in the project root directory
- Check if all dependencies are installed correctly
- Confirm paths include `core/` prefix

### Docker Test Issues

- Rebuild Docker image after code changes (`make build`)
- Check Docker logs for detailed error messages
- Verify Docker daemon is running
- Ensure `.env` file exists and is properly configured
