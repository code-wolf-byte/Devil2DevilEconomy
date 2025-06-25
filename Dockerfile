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
    gunicorn==21.2.0 \
    python-dotenv==1.0.0 \
    Werkzeug==2.3.7 \
    SQLAlchemy==2.0.21 \
    alembic==1.12.0 \
    requests==2.31.0 \
    Pillow==10.0.1 \
    cryptography==41.0.7

# Create necessary directories
RUN mkdir -p instance static/uploads

# Copy application code
COPY . .

# Ensure upload directory exists and has proper permissions
RUN chmod -R 755 static/uploads && \
    chown -R root:root static/uploads

# Expose port
EXPOSE 5000

# Run the application
CMD ["gunicorn", "--bind", "0.0.0.0:5000", "--timeout", "120", "--workers", "1", "main:app"] 