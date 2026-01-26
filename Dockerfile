FROM node:18-alpine AS react-build

WORKDIR /react

COPY asu-unity-react/package.json asu-unity-react/yarn.lock asu-unity-react/.yarnrc.yml /react/
COPY asu-unity-react/.yarn /react/.yarn

RUN corepack enable && yarn install --immutable

COPY asu-unity-react/public /react/public
COPY asu-unity-react/src /react/src
COPY asu-unity-react/index.html /react/index.html
COPY asu-unity-react/vite.config.js /react/vite.config.js

ARG VITE_API_BASE_URL=
ENV VITE_API_BASE_URL=$VITE_API_BASE_URL

RUN yarn build

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

# Create necessary directories
RUN mkdir -p instance static/uploads

# Copy application code
COPY . .

# Copy React build output
COPY --from=react-build /react/dist /app/react-dist

# Location of the built React app for Flask to serve
ENV REACT_BUILD_DIR=/app/react-dist

# Set proper permissions for directories
RUN chmod -R 755 /app && \
    chmod -R 777 static/uploads && \
    chmod -R 777 instance

# Run as root (traditional Docker approach) - avoids all permission issues

# Expose port
EXPOSE 5000

# Run the application with Flask development server
CMD ["python3", "main.py"] 
