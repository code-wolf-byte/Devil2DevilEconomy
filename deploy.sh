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
# Check both possible locations: instance/store.db (primary) and store.db (legacy)
for db_path in "instance/store.db" "store.db"; do
    if [ -f "$db_path" ]; then
        print_status "Setting database permissions for $db_path..."
        
        # Check current owner
        DB_OWNER=$(stat -c '%U' "$db_path" 2>/dev/null || echo "unknown")
        print_status "Current database owner: $DB_OWNER"
        
        # If database is owned by root, we need sudo to change it
        if [ "$DB_OWNER" = "root" ]; then
            print_warning "Database is owned by root, fixing ownership..."
            if command -v sudo >/dev/null 2>&1; then
                sudo chown $(whoami):$(whoami) "$db_path"
                print_success "Changed database ownership from root to $(whoami)"
            else
                print_error "Database is owned by root but sudo not available. Manual fix required."
            fi
        else
            # Standard ownership change
            chown $(whoami):$(whoami) "$db_path" 2>/dev/null || true
        fi
        
        # Set permissions (664 = rw-rw-r-- allows read/write for owner and group)
        chmod 664 "$db_path"
        
        # Verify final permissions
        FINAL_PERMS=$(stat -c '%a' "$db_path" 2>/dev/null || echo "unknown")
        FINAL_OWNER=$(stat -c '%U:%G' "$db_path" 2>/dev/null || echo "unknown")
        print_success "Database permissions set for $db_path: $FINAL_PERMS ($FINAL_OWNER)"
    fi
done

# Set proper permissions for uploads directories
print_status "Setting uploads directory permissions..."

# Handle static/uploads directory
if [ -d "static/uploads" ]; then
    UPLOADS_OWNER=$(stat -c '%U' static/uploads 2>/dev/null || echo "unknown")
    print_status "Current static/uploads owner: $UPLOADS_OWNER"
    
    if [ "$UPLOADS_OWNER" = "root" ]; then
        print_warning "Uploads directory is owned by root, fixing ownership..."
        if command -v sudo >/dev/null 2>&1; then
            sudo chown -R $(whoami):$(whoami) static/uploads
            print_success "Changed uploads ownership from root to $(whoami)"
        else
            print_error "Uploads directory is owned by root but sudo not available. Manual fix required."
        fi
    else
        chown -R $(whoami):$(whoami) static/uploads 2>/dev/null || true
    fi
    
    # Set permissions (775 = rwxrwxr-x allows read/write/execute for owner and group)
    chmod -R 775 static/uploads
    
    FINAL_PERMS=$(stat -c '%a' static/uploads 2>/dev/null || echo "unknown")
    FINAL_OWNER=$(stat -c '%U:%G' static/uploads 2>/dev/null || echo "unknown")
    print_success "static/uploads permissions set: $FINAL_PERMS ($FINAL_OWNER)"
fi

# Handle uploads directory (if it exists)
if [ -d "uploads" ]; then
    UPLOADS_OWNER=$(stat -c '%U' uploads 2>/dev/null || echo "unknown")
    print_status "Current uploads owner: $UPLOADS_OWNER"
    
    if [ "$UPLOADS_OWNER" = "root" ]; then
        print_warning "uploads directory is owned by root, fixing ownership..."
        if command -v sudo >/dev/null 2>&1; then
            sudo chown -R $(whoami):$(whoami) uploads
            print_success "Changed uploads ownership from root to $(whoami)"
        else
            print_error "uploads directory is owned by root but sudo not available. Manual fix required."
        fi
    else
        chown -R $(whoami):$(whoami) uploads 2>/dev/null || true
    fi
    
    chmod -R 775 uploads
    
    FINAL_PERMS=$(stat -c '%a' uploads 2>/dev/null || echo "unknown")
    FINAL_OWNER=$(stat -c '%U:%G' uploads 2>/dev/null || echo "unknown")
    print_success "uploads permissions set: $FINAL_PERMS ($FINAL_OWNER)"
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
        
        # Check upload capability
        UPLOAD_WRITABLE="❌"
        if [ -d "static/uploads" ] && [ -w "static/uploads" ]; then
            UPLOAD_WRITABLE="✅"
        fi
        echo "   • Upload Capability: $UPLOAD_WRITABLE $([ "$UPLOAD_WRITABLE" = "✅" ] && echo "Ready" || echo "Check permissions")"
        echo "   • Permissions: ✅ Verified and fixed"
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