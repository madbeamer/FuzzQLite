# Use the provided image as base
FROM theosotr/sqlite3-test

# Switch to root user for package installation
USER root

# Set environment variables
ENV DEBIAN_FRONTEND=noninteractive
ENV PYTHONUNBUFFERED=1
ENV PYTHONPATH=/app

# Install any additional dependencies
RUN apt-get update && apt-get install -y \
    python3 \
    python3-pip \
    build-essential \
    wget \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# Install latest SQLite version as a reference
WORKDIR /tmp
RUN wget https://www.sqlite.org/2025/sqlite-autoconf-3490100.tar.gz && \
    tar -xzf sqlite-autoconf-3490100.tar.gz && \
    cd sqlite-autoconf-3490100 && \
    ./configure && make && make install && \
    cp /usr/local/bin/sqlite3 /usr/bin/sqlite3-latest

# Create app directory
WORKDIR /app

# Copy requirements and install Python dependencies
COPY requirements.txt .
RUN pip3 install --no-cache-dir -r requirements.txt

# Copy source code and tests
COPY src/ /app/src/

# Make main.py executable
RUN chmod +x /app/src/main.py

# Create symbolic link for the main executable
RUN ln -sf /app/src/main.py /usr/bin/test-db

# Entry point
ENTRYPOINT ["python3", "/app/src/main.py"]
