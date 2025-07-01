FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements and install Python dependencies
COPY requirements.txt .

# Install only essential Flask/Discord dependencies
RUN pip install --no-cache-dir \
    Flask==2.3.3 \
    Flask-SQLAlchemy==3.0.5 \
    Flask-Login==0.6.3 \
    Flask-Migrate==4.0.5 \
    discord.py==2.3.2 \
    python-dotenv==1.0.0 \
    Werkzeug==2.3.7 \
    SQLAlchemy==2.0.21 \
    alembic==1.12.0 \
    requests==2.31.0 \
    Pillow==10.0.1 \
    cryptography==41.0.7

# Create a non-root user with matching UID/GID to host ubuntu user (1000:1000)
RUN groupadd -g 1000 appuser && useradd -u 1000 -g 1000 appuser

# Create necessary directories with proper ownership
RUN mkdir -p instance static/uploads

# Copy application code
COPY . .

# Set proper ownership and permissions for non-root user
# Make sure uploads directory is writable by appuser
RUN chown -R appuser:appuser /app && \
    chmod -R 755 /app && \
    chmod -R 775 static/uploads

# Switch to non-root user
USER appuser

# Expose port
EXPOSE 5000

# Run the application with Flask development server
CMD ["python3", "main.py"] 