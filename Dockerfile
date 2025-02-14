# Use the official Python image as the base image
FROM python:3.8-slim AS base

# Set the working directory inside the container
WORKDIR /app

# Install system dependencies
RUN apt-get update && \
    apt-get install -y wget unzip curl gnupg procps && \
    curl -s https://ngrok-agent.s3.amazonaws.com/ngrok.asc | \
    gpg --dearmor -o /etc/apt/keyrings/ngrok.gpg && \
    echo "deb [signed-by=/etc/apt/keyrings/ngrok.gpg] https://ngrok-agent.s3.amazonaws.com buster main" | \
    tee /etc/apt/sources.list.d/ngrok.list && \
    apt-get update && \
    apt-get install -y ngrok && \
    rm -rf /var/lib/apt/lists/*  # Clean up apt cache

# Set up ngrok authtoken (using the v3.x command)
ARG NGROK_AUTHTOKEN
RUN ngrok config add-authtoken "${NGROK_AUTHTOKEN}"

# Install virtualenv and create virtual environment
RUN pip install virtualenv && \
    python -m virtualenv /venv
ENV VIRTUAL_ENV=/venv
ENV PATH="$VIRTUAL_ENV/bin:$PATH"

# Install Python dependencies
COPY core/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy only necessary files
COPY core/ core/
COPY entrypoint.sh .
RUN chmod +x entrypoint.sh

# Expose application and ngrok API ports
EXPOSE 5001 4040

# Test Stage
FROM base AS test
CMD ["pytest", "core/tests"]

# Production Stage
FROM base AS production
ENTRYPOINT ["/app/entrypoint.sh"]
CMD ["python", "core/run.py"]
