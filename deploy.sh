#!/bin/bash

# Devil2DevilEconomy Deployment Script
# This script deploys the Flask application with database and uploads preservation

set -e  # Exit on any error

echo "🚀 Starting Devil2DevilEconomy deployment..."

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Function to print colored output
print_status() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

print_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Check if running as root or with sudo
if [[ $EUID -eq 0 ]]; then
    DOCKER_CMD="docker"
    DOCKER_COMPOSE_CMD="docker compose"
else
    DOCKER_CMD="sudo docker"
    DOCKER_COMPOSE_CMD="sudo docker compose"
fi

# Stop existing containers
print_status "Stopping existing containers..."
$DOCKER_COMPOSE_CMD down 2>/dev/null || true

# Create necessary directories
print_status "Creating necessary directories..."
mkdir -p instance
mkdir -p static/uploads
mkdir -p data_backup

# Backup existing data if it exists
if [ -f "store.db" ]; then
    print_status "Backing up existing database..."
    cp store.db data_backup/store.db.backup.$(date +%Y%m%d_%H%M%S)
elif [ -f "instance/store.db" ]; then
    print_status "Backing up existing database from instance directory..."
    cp instance/store.db data_backup/store.db.backup.$(date +%Y%m%d_%H%M%S)
fi

# Remove any existing store.db directory (if it was created incorrectly)
if [ -d "store.db" ]; then
    print_warning "Removing incorrect store.db directory..."
    rm -rf store.db
fi

# Copy database file to the correct location
if [ -f "instance/store.db" ]; then
    print_status "Copying database from instance directory..."
    cp instance/store.db ./store.db
elif [ ! -f "store.db" ]; then
    print_warning "No database file found. Application will create a new one."
fi

# Set proper permissions for database file
if [ -f "store.db" ]; then
    print_status "Setting database permissions..."
    chmod 644 store.db
    chown $(whoami):$(whoami) store.db 2>/dev/null || true
fi

# Set proper permissions for uploads directory
print_status "Setting uploads directory permissions..."
chmod -R 755 static/uploads
chown -R $(whoami):$(whoami) static/uploads 2>/dev/null || true

# Set proper permissions for instance directory
chmod -R 755 instance
chown -R $(whoami):$(whoami) instance 2>/dev/null || true

# Build and start the application
print_status "Building Docker image..."
$DOCKER_COMPOSE_CMD build

print_status "Starting application..."
$DOCKER_COMPOSE_CMD up -d

# Wait a moment for the container to start
sleep 3

# Check if container is running
if $DOCKER_COMPOSE_CMD ps | grep -q "Up"; then
    print_success "Container is running!"
    
    # Test the application
    print_status "Testing application..."
    if curl -s -o /dev/null -w "%{http_code}" http://localhost:5000 | grep -q "200\|302\|404"; then
        print_success "Application is responding!"
        print_success "🎉 Deployment completed successfully!"
        echo ""
        echo "📋 Deployment Summary:"
        echo "   • Application URL: http://localhost:5000"
        echo "   • Database: $([ -f "store.db" ] && echo "✅ Present" || echo "⚠️  Will be created")"
        echo "   • Uploads: $([ -d "static/uploads" ] && echo "✅ Directory ready" || echo "⚠️  Directory created")"
        echo ""
        echo "📊 Container Status:"
        $DOCKER_COMPOSE_CMD ps
        echo ""
        echo "📝 To view logs: $DOCKER_COMPOSE_CMD logs -f"
        echo "🛑 To stop: $DOCKER_COMPOSE_CMD down"
    else
        print_warning "Application started but may have issues. Check logs:"
        $DOCKER_COMPOSE_CMD logs --tail=20
    fi
else
    print_error "Container failed to start. Check logs:"
    $DOCKER_COMPOSE_CMD logs
    exit 1
fi 