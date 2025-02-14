# Use the official Python image as the base image
FROM python:3.8-slim AS base

# Set the working directory inside the container
WORKDIR /app

# Install dependencies
RUN apt-get update && \
    apt-get install -y wget unzip curl gnupg procps && \
    curl -s https://ngrok-agent.s3.amazonaws.com/ngrok.asc | \
    gpg --dearmor -o /etc/apt/keyrings/ngrok.gpg && \
    echo "deb [signed-by=/etc/apt/keyrings/ngrok.gpg] https://ngrok-agent.s3.amazonaws.com buster main" | \
    tee /etc/apt/sources.list.d/ngrok.list && \
    apt-get update && \
    apt-get install -y ngrok

# Set up ngrok authtoken (using the v3.x command)
ARG NGROK_AUTHTOKEN
RUN ngrok config add-authtoken "${NGROK_AUTHTOKEN}"

# Install virtualenv to manage Python dependencies inside the container
RUN pip install virtualenv

# Create a persistent virtual environment outside the codebase directory
RUN python -m virtualenv /venv
ENV VIRTUAL_ENV=/venv
ENV PATH="$VIRTUAL_ENV/bin:$PATH"

# Install dependencies inside the virtual environment
COPY core/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy the codebase to the container
COPY . .

# Expose application and ngrok API ports
EXPOSE 5001 4040

# Test Stage
FROM base AS test

# Run unit tests with pytest
CMD ["pytest", "core/tests"]

# Production Stage
FROM base AS production

# Copy entrypoint script and set permissions
COPY entrypoint.sh /app/entrypoint.sh
RUN chmod +x /app/entrypoint.sh

# Copy the codebase to the production stage
COPY --from=base /app /app

# Set entrypoint
ENTRYPOINT ["/app/entrypoint.sh"]

# Command to run the application
CMD ["python", "core/run.py"]
