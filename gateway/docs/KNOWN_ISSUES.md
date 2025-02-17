# Known Issues

## Gateway Registration

### URL Encoding Issue with API Keys

- **Issue**: The Gateway registration fails with 404 errors when API keys contain special characters (/, +) due to improper URL encoding.
- **Impact**: Core components continue to function locally, but Gateway registration may fail.
- **Workaround**: The API remains usable locally despite Gateway registration failure.
- **Status**: Under investigation
- **First Reported**: 2025-02-17
- **Logs**:
  ```
  ERROR - Attempt 1 failed: 404 Client Error: Not Found for url: https://codequery.dev/ngrok-urls/[API_KEY]
  ```
