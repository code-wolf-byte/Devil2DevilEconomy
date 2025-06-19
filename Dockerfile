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

# Copy sample skin files if they exist
COPY --chown=app:app static/uploads/skins/ static/uploads/skins/

# Set proper permissions for upload directories
RUN chmod -R 755 static/uploads/ && \
    chmod -R 644 static/uploads/skins/* || true

# Create .env file template if it doesn't exist
RUN if [ ! -f .env ]; then \
    echo "# Docker Environment Configuration" > .env && \
    echo "DISCORD_TOKEN=your_discord_bot_token_here" >> .env && \
    echo "DISCORD_CLIENT_ID=your_discord_client_id_here" >> .env && \
    echo "DISCORD_CLIENT_SECRET=your_discord_client_secret_here" >> .env && \
    echo "DISCORD_REDIRECT_URI=http://localhost:6000/callback" >> .env && \
    echo "SECRET_KEY=docker_secret_key_change_in_production" >> .env && \
    echo "DATABASE_URL=sqlite:///store.db" >> .env && \
    echo "GUILD_ID=your_guild_id_here" >> .env && \
    echo "GENERAL_CHANNEL_ID=your_general_channel_id_here" >> .env && \
    echo "VERIFIED_ROLE_ID=your_verified_role_id_here" >> .env && \
    echo "ONBOARDING_ROLE_IDS=role1_id,role2_id,role3_id" >> .env; \
    fi

# Switch to non-root user
USER app

# Expose the port the app runs on
EXPOSE 6000

# Health check
HEALTHCHECK --interval=30s --timeout=30s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:6000/ || exit 1

# Run the application
CMD ["python", "app.py"] 