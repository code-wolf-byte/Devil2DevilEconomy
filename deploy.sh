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
mkdir -p uploads
mkdir -p data_backup

# Backup existing data if it exists
if [ -f "store.db" ]; then
    print_status "Backing up existing database..."
    cp store.db data_backup/store.db.backup.$(date +%Y%m%d_%H%M%S)
elif [ -f "instance/store.db" ]; then
    print_status "Backing up existing database from instance directory..."
    cp instance/store.db data_backup/store.db.backup.$(date +%Y%m%d_%H%M%S)
fi

# Backup existing uploads
if [ "$(ls -A static/uploads 2>/dev/null)" ]; then
    print_status "Backing up existing uploads from static/uploads..."
    cp -r static/uploads data_backup/static_uploads_backup.$(date +%Y%m%d_%H%M%S) 2>/dev/null || true
fi

if [ "$(ls -A uploads 2>/dev/null)" ]; then
    print_status "Backing up existing uploads from uploads directory..."
    cp -r uploads data_backup/uploads_backup.$(date +%Y%m%d_%H%M%S) 2>/dev/null || true
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

# Set proper permissions for database files
# Traditional approach: ensure files are readable/writable
for db_path in "instance/store.db" "store.db"; do
    if [ -f "$db_path" ]; then
        print_status "Setting database permissions for $db_path..."
        
        # Set liberal permissions for container access (root container can write to anything)
        chmod 666 "$db_path" 2>/dev/null || true
        
        print_success "Database permissions set for $db_path (traditional Docker approach)"
    fi
done

# Set proper permissions for uploads directories
print_status "Setting uploads directory permissions..."

# Traditional approach: set liberal permissions for container access
if [ -d "static/uploads" ]; then
    chmod -R 777 static/uploads 2>/dev/null || true
    print_success "static/uploads permissions set (traditional Docker approach)"
fi

if [ -d "uploads" ]; then
    chmod -R 777 uploads 2>/dev/null || true
    print_success "uploads permissions set (traditional Docker approach)"
fi

# Set proper permissions for instance directory
chmod -R 755 instance
chown -R $(whoami):$(whoami) instance 2>/dev/null || true

# Count upload files
STATIC_UPLOAD_COUNT=$(find static/uploads -type f 2>/dev/null | wc -l)
UPLOAD_COUNT=$(find uploads -type f 2>/dev/null | wc -l)

print_status "Found $STATIC_UPLOAD_COUNT files in static/uploads"
print_status "Found $UPLOAD_COUNT files in uploads directory"

# Build and start the application
print_status "Building Docker image..."
$DOCKER_COMPOSE_CMD build

print_status "Starting application..."
$DOCKER_COMPOSE_CMD up -d

# Wait a moment for the container to start
sleep 3

# Post-deployment permission fixes
print_status "Running post-deployment permission checks..."

# Fix any permission issues that might have occurred during Docker volume mounting
for db_path in "instance/store.db" "store.db"; do
    if [ -f "$db_path" ]; then
        # Ensure database is still writable after Docker mount
        DB_WRITABLE=$(test -w "$db_path" && echo "yes" || echo "no")
        if [ "$DB_WRITABLE" = "no" ]; then
            print_warning "Database $db_path is not writable after container start, fixing..."
            chmod 664 "$db_path"
            if command -v sudo >/dev/null 2>&1 && [ "$(stat -c '%U' "$db_path")" = "root" ]; then
                sudo chown $(whoami):$(whoami) "$db_path"
            fi
        fi
        print_status "Database $db_path writable: $DB_WRITABLE"
    fi
done

# Ensure uploads directories are writable
for dir in "static/uploads" "uploads" "instance"; do
    if [ -d "$dir" ]; then
        DIR_WRITABLE=$(test -w "$dir" && echo "yes" || echo "no")
        if [ "$DIR_WRITABLE" = "no" ]; then
            print_warning "$dir is not writable after container start, fixing..."
            
            # Check if owned by root and fix with sudo if needed
            DIR_OWNER=$(stat -c '%U' "$dir" 2>/dev/null || echo "unknown")
            if [ "$DIR_OWNER" = "root" ] && command -v sudo >/dev/null 2>&1; then
                sudo chown -R $(whoami):$(whoami) "$dir"
                print_status "Fixed root ownership for $dir"
            else
                chown -R $(whoami):$(whoami) "$dir" 2>/dev/null || true
            fi
            
            # Set appropriate permissions (775 for uploads, 755 for instance)
            if [[ "$dir" == *"uploads"* ]]; then
                chmod -R 775 "$dir"  # Upload directories need write access
            else
                chmod -R 755 "$dir"  # Other directories
            fi
        fi
        print_status "$dir writable: $DIR_WRITABLE"
    fi
done

# Check if container is running
if $DOCKER_COMPOSE_CMD ps | grep -q "Up"; then
    print_success "Container is running!"
    
    # Test container capabilities (traditional Docker approach)
    print_status "Testing container capabilities..."
    
    CONTAINER_NAME=$(docker ps -q -f name=devil2devileconomy-web)
    if [ -n "$CONTAINER_NAME" ]; then
        # Test container write capability
        if $DOCKER_CMD exec $CONTAINER_NAME touch /app/static/uploads/deployment_test.txt 2>/dev/null; then
            $DOCKER_CMD exec $CONTAINER_NAME rm /app/static/uploads/deployment_test.txt 2>/dev/null
            print_success "Container can write to uploads directory ✅"
        else
            print_error "Container cannot write to uploads directory ❌"
        fi
        
        # Test database write capability
        if $DOCKER_CMD exec $CONTAINER_NAME python3 -c "
import sqlite3
import os
db_path = 'instance/store.db' if os.path.exists('instance/store.db') else 'store.db'
if os.path.exists(db_path):
    conn = sqlite3.connect(db_path)
    conn.execute('SELECT 1')
    conn.close()
    print('Database accessible')
" 2>/dev/null; then
            print_success "Container can access database ✅"
        else
            print_error "Container cannot access database ❌"
        fi
    fi
    
    # Verify uploads are mounted correctly
    print_status "Verifying upload files are accessible in container..."
    CONTAINER_STATIC_COUNT=$($DOCKER_CMD exec $(docker ps -q -f name=devil2devileconomy-web) find /app/static/uploads -type f 2>/dev/null | wc -l || echo "0")
    CONTAINER_UPLOAD_COUNT=$($DOCKER_CMD exec $(docker ps -q -f name=devil2devileconomy-web) find /app/uploads -type f 2>/dev/null | wc -l || echo "0")
    
    print_status "Container has $CONTAINER_STATIC_COUNT files in /app/static/uploads"
    print_status "Container has $CONTAINER_UPLOAD_COUNT files in /app/uploads"
    
    # Test the application
    print_status "Testing application..."
    if curl -s -o /dev/null -w "%{http_code}" http://localhost:5000 | grep -q "200\|302\|404"; then
        print_success "Application is responding!"
        print_success "🎉 Deployment completed successfully!"
        echo ""
        echo "📋 Deployment Summary:"
        echo "   • Application URL: http://localhost:5000"
        
        # Check for database in correct location (instance/store.db is primary)
        if [ -f "instance/store.db" ]; then
            DB_PERMS=$(stat -c '%a' instance/store.db 2>/dev/null || echo "unknown")
            DB_OWNER=$(stat -c '%U:%G' instance/store.db 2>/dev/null || echo "unknown")
            echo "   • Database: ✅ Present at instance/store.db ($DB_PERMS, $DB_OWNER)"
        elif [ -f "store.db" ]; then
            DB_PERMS=$(stat -c '%a' store.db 2>/dev/null || echo "unknown")
            DB_OWNER=$(stat -c '%U:%G' store.db 2>/dev/null || echo "unknown")
            echo "   • Database: ✅ Present at store.db ($DB_PERMS, $DB_OWNER)"
        else
            echo "   • Database: ⚠️  Will be created"
        fi
        echo "   • Static Uploads: ✅ $STATIC_UPLOAD_COUNT files mounted"
        echo "   • Upload Directory: ✅ $UPLOAD_COUNT files mounted"
        
        # Traditional Docker status
        echo "   • Docker Approach: ✅ Traditional root-based (simple and reliable)"
        echo "   • File Permissions: ✅ Liberal permissions set (777)"
        echo "   • Database Permissions: ✅ Liberal permissions set (666)"
        echo ""
        echo "📊 Container Status:"
        $DOCKER_COMPOSE_CMD ps
        echo ""
        echo "📝 To view logs: $DOCKER_COMPOSE_CMD logs -f"
        echo "🛑 To stop: $DOCKER_COMPOSE_CMD down"
        echo ""
        echo "🔧 Troubleshooting:"
        echo "   • File upload issues: Run 'chmod -R 777 static/uploads/'"
        echo "   • Database write issues: Run 'chmod 666 instance/store.db'"
        echo "   • Permission problems: Re-run this deployment script"
        echo "   • Traditional approach: Container runs as root for simplicity"
    else
        print_warning "Application started but may have issues. Check logs:"
        $DOCKER_COMPOSE_CMD logs --tail=20
    fi
else
    print_error "Container failed to start. Check logs:"
    $DOCKER_COMPOSE_CMD logs
    exit 1
fi 