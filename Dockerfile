# Dockerfile

# Use a slim python base image
FROM python:3.11-slim AS runtime

# Ensure we dont have interactive prompts

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONBUFFERED=1

WORKDIR /app

COPY requirements.txt . 
RUN pip install --no-cache-dri -r requirements.txt

# Copy source code
COPY src/ src/

# Default entrypoint: run the aggregator CLI. 
# It reads from a file argument if given, otherwise from stdin.
ENTRYPOINT ["python", "src/main.py"]

