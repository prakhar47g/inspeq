# Stage 1: Build dependencies
FROM python:3.9-slim AS builder

# Install system dependencies for building Python packages
RUN apt-get update && \
    apt-get install -y \
    build-essential \
    libffi-dev \
    gcc \
    make \
    && rm -rf /var/lib/apt/lists/*

# Set the working directory and copy requirements
WORKDIR /app
COPY requirements.txt ./

# Install Python dependencies in the builder stage
RUN pip install --no-cache-dir -r requirements.txt

# Stage 2: Final runtime image
FROM python:3.9-slim

# Copy the installed dependencies from the builder stage
COPY --from=builder /usr/local /usr/local

# Set up app directory and copy the code
ENV APP_HOME /app
WORKDIR $APP_HOME
COPY server.py ./

# Run the server
CMD ["python", "server.py"]

