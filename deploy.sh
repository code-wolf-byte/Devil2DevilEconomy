#!/bin/bash

# Economy Bot Deployment Script
# This script helps deploy the Economy Bot using Docker

set -e

echo "🚀 Economy Bot Deployment Script"
echo "================================="

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Function to print colored output
print_status() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Check if Docker is installed
if ! command -v docker &> /dev/null; then
    print_error "Docker is not installed. Please install Docker first."
    exit 1
fi

# Check if Docker Compose is installed
if ! command -v docker-compose &> /dev/null && ! docker compose version &> /dev/null; then
    print_error "Docker Compose is not installed. Please install Docker Compose first."
    exit 1
fi

print_status "Docker and Docker Compose are installed."

# Create necessary directories
print_status "Creating necessary directories..."
mkdir -p data logs uploads

# Check if .env file exists
if [ ! -f .env ]; then
    print_warning ".env file not found. Creating template..."
    cat > .env << EOF
# Discord Bot Configuration
# Get these from Discord Developer Portal: https://discord.com/developers/applications
DISCORD_TOKEN=your_discord_bot_token_here
DISCORD_CLIENT_ID=your_discord_client_id_here
DISCORD_CLIENT_SECRET=your_discord_client_secret_here
DISCORD_REDIRECT_URI=http://localhost:6000/callback

# Flask Configuration
SECRET_KEY=$(openssl rand -hex 32)

# Database Configuration
DATABASE_URL=sqlite:///store.db

# Guild Configuration (Optional - for Discord server integration)
GUILD_ID=your_guild_id_here
GENERAL_CHANNEL_ID=your_general_channel_id_here

# Role Configuration for Economy System (Optional)
VERIFIED_ROLE_ID=your_verified_role_id_here
ONBOARDING_ROLE_IDS=role1_id,role2_id,role3_id
EOF
    print_warning "Please edit the .env file with your Discord bot credentials before continuing."
    print_warning "You can get Discord credentials from: https://discord.com/developers/applications"
    echo
    read -p "Press Enter when you have configured the .env file..."
fi

# Validate .env file
if grep -q "your_discord_bot_token_here" .env; then
    print_error "Please configure your Discord bot credentials in the .env file first!"
    exit 1
fi

print_status ".env file configured."

# Build and start the application
print_status "Building Docker image..."
docker-compose build

print_status "Starting Economy Bot..."
docker-compose up -d

# Wait for the application to start
print_status "Waiting for application to start..."
sleep 10

# Check if the application is running
if docker-compose ps | grep -q "Up"; then
    print_status "✅ Economy Bot is running!"
    echo
    echo "🌐 Application URLs:"
    echo "   - Main Application: http://localhost:6000"
    echo "   - Admin Panel: http://localhost:6000/admin"
    echo
    echo "📊 Useful Commands:"
    echo "   - View logs: docker-compose logs -f"
    echo "   - Stop application: docker-compose down"
    echo "   - Restart application: docker-compose restart"
    echo "   - Update application: docker-compose pull && docker-compose up -d"
    echo
    echo "📁 Data Locations:"
    echo "   - Database: ./data/"
    echo "   - Uploads: ./uploads/"
    echo "   - Logs: ./logs/"
    echo
    print_status "Setup complete! Check the logs if you encounter any issues."
else
    print_error "❌ Failed to start Economy Bot. Check the logs:"
    docker-compose logs
    exit 1
fi 