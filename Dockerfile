# Use Python 3.12 slim image for smaller size
FROM python:3.12-slim

# Set environment variables
ENV PYTHONUNBUFFERED=1
ENV PYTHONDONTWRITEBYTECODE=1
ENV FLASK_APP=app.py
ENV FLASK_ENV=production
ENV DOCKER_ENV=1

# Set work directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    libffi-dev \
    libssl-dev \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Create application user (security best practice)
RUN useradd --create-home --shell /bin/bash app

# Copy requirements first for better caching
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# Create necessary directories with proper permissions
RUN mkdir -p static/uploads/skins \
    static/uploads/content \
    static/uploads/documents \
    static/uploads/misc \
    logs \
    instance \
    migrations/versions && \
    chown -R app:app /app && \
    chmod -R 755 logs

# Copy application code
COPY --chown=app:app . .

# Set proper permissions for upload directories
RUN chmod -R 755 static/uploads/ || true

# Note: .env file should be provided by the user before building

# Switch to non-root user
USER app

# Expose the port the app runs on
EXPOSE 6000

# Health check
HEALTHCHECK --interval=30s --timeout=30s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:6000/ || exit 1

# Run the application
CMD ["python", "app.py"] 