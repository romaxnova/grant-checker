# ---- Base image for all AGENTS ----
FROM python:3.12-slim

# System dependencies (add more as needed for all agents)
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
        build-essential \
        curl \
        git \
        libglib2.0-0 \
        libnss3 \
        libgconf-2-4 \
        libfontconfig1 \
        libxss1 \
        libasound2 \
        libxtst6 \
        libxrandr2 \
        libgtk-3-0 \
        ca-certificates \
    && rm -rf /var/lib/apt/lists/*

# Set workdir
WORKDIR /app

# Copy requirements and install Python deps
COPY requirements.txt ./
RUN pip install --upgrade pip && pip install -r requirements.txt

# Copy the rest of the agent code
COPY . .

# Default command (can be overridden in CI/CD)
CMD ["python", "grants_monitor.py"]
