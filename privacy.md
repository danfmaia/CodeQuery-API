# Privacy Policy for AutocoderGPT

Effective Date: September 8, 2024

## Introduction

**AutocoderGPT** is a tool designed to help developers interact with a project's codebase by providing access to file structures and contents. This Privacy Policy outlines how the API handles data during the process, ensuring transparency about the temporary nature of the data usage.

## What Data Is Processed

When using the **AutocoderGPT** API, certain data is processed temporarily to fulfill requests:

- **File Paths**: The API processes the paths of files in the project.
- **File Contents**: If requested through the `/files/content` endpoint, the API processes the content of those files.

None of this data is stored—it's processed in real-time and discarded once the response is generated.

## How Data Is Used

The **AutocoderGPT** API processes the data only to provide the requested information about file structures or contents. The data is used solely for responding to the API request and is not used for any other purpose.

## Data Retention

There is no data retention. All data, including file paths and contents, is processed on-the-fly and discarded immediately after the API returns the response.

## Sharing of Information

Since no data is stored or logged, there is no data available to share with third parties.

## Security

The API is designed for local development environments and temporary use with tools like **ngrok**. Since it's intended for controlled and short-term exposure, no advanced security features are built-in. If you plan to expose the API for longer periods or in less controlled environments, consider adding minimal security measures like API keys or basic authentication to restrict access.

## Changes to This Policy

This Privacy Policy may be updated periodically. Changes will be posted here with the updated effective date.

## Contact

If you have any questions or concerns regarding this Privacy Policy, please create an issue on the GitHub repository: https://github.com/yourusername/autocoder-gpt-api/issues.
