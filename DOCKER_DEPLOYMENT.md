# Docker Deployment Guide for Economy Bot

This guide will help you deploy the Economy Bot application using Docker for easy setup and management.

## 🐳 Quick Start

### Prerequisites
- Docker (version 20.10 or higher)
- Docker Compose (version 2.0 or higher)
- Discord Application credentials

### 1. Clone and Setup
```bash
git clone <your-repository>
cd Economy
chmod +x deploy.sh
./deploy.sh
```

The deployment script will:
- Check Docker installation
- Create necessary directories
- Generate .env template
- Build and start the application
- Optionally set up production mode with Nginx

### 2. Manual Setup (Alternative)

If you prefer manual setup:

```bash
# Create directories
mkdir -p data logs uploads ssl

# Create .env file (see configuration section below)
cp env.example .env
# Edit .env with your Discord credentials

# Build and start
docker-compose build
docker-compose up -d
```

## ⚙️ Configuration

### Environment Variables (.env file)
```env
# Discord Bot Configuration (REQUIRED)
DISCORD_TOKEN=your_discord_bot_token_here
DISCORD_CLIENT_ID=your_discord_client_id_here
DISCORD_CLIENT_SECRET=your_discord_client_secret_here
DISCORD_REDIRECT_URI=http://localhost:6000/callback

# Flask Configuration
SECRET_KEY=your_secret_key_here

# Database Configuration
DATABASE_URL=sqlite:///store.db

# Optional: Discord Server Configuration
GUILD_ID=your_guild_id_here
GENERAL_CHANNEL_ID=your_general_channel_id_here
VERIFIED_ROLE_ID=your_verified_role_id_here
ONBOARDING_ROLE_IDS=role1_id,role2_id,role3_id
```

### Getting Discord Credentials
1. Go to [Discord Developer Portal](https://discord.com/developers/applications)
2. Create a new application
3. Go to "Bot" section and create a bot
4. Copy the token to `DISCORD_TOKEN`
5. Go to "OAuth2" section for `CLIENT_ID` and `CLIENT_SECRET`
6. Add redirect URI: `http://your-domain.com/callback`

## 🚀 Deployment Options

### Development Mode
```bash
docker-compose up -d
```
- Runs on port 6000
- Direct access to Flask application
- Suitable for development and testing

### Production Mode
```bash
docker-compose --profile production up -d
```
- Includes Nginx reverse proxy
- SSL/HTTPS support
- Rate limiting and security headers
- Runs on ports 80 (HTTP) and 443 (HTTPS)

## 📁 Directory Structure

```
Economy/
├── Dockerfile              # Main application container
├── docker-compose.yml      # Container orchestration
├── nginx.conf             # Nginx configuration for production
├── deploy.sh              # Automated deployment script
├── .dockerignore          # Files to exclude from Docker build
├── data/                  # Persistent database storage
├── logs/                  # Application logs
├── uploads/               # User uploaded files (Minecraft skins, etc.)
└── ssl/                   # SSL certificates for HTTPS
```

## 🔧 Management Commands

### Basic Operations
```bash
# View logs
docker-compose logs -f

# Stop application
docker-compose down

# Restart application
docker-compose restart

# Update application
docker-compose pull && docker-compose up -d --build

# View running containers
docker-compose ps
```

### Database Management
```bash
# Access database
docker-compose exec economy-bot sqlite3 /app/instance/store.db

# Backup database
docker-compose exec economy-bot cp /app/instance/store.db /app/logs/backup_$(date +%Y%m%d_%H%M%S).db

# View database in host
sqlite3 data/store.db
```

### File Management
```bash
# Upload Minecraft skins
cp your_skin.png uploads/skins/

# View uploaded files
ls -la uploads/

# Check application files
docker-compose exec economy-bot ls -la /app/static/uploads/
```

## 🛡️ Security Features

### Container Security
- Non-root user execution
- Read-only environment files
- Isolated network
- Health checks

### Application Security
- Secure file downloads with tokens
- Rate limiting on API endpoints
- HTTPS redirect in production
- Security headers (HSTS, X-Frame-Options, etc.)

### File Upload Security
- File type validation
- Secure file serving
- Directory traversal protection
- Size limits (20MB max)

## 🔍 Troubleshooting

### Common Issues

#### 1. Container Won't Start
```bash
# Check logs
docker-compose logs economy-bot

# Common causes:
# - Missing .env file
# - Invalid Discord credentials
# - Port conflicts
```

#### 2. Database Issues
```bash
# Reset database
docker-compose down
rm -rf data/
docker-compose up -d

# The application will recreate tables automatically
```

#### 3. Discord Bot Not Working
```bash
# Check bot permissions in Discord server
# Verify GUILD_ID in .env
# Ensure bot has "Manage Roles" permission
```

#### 4. File Upload Issues
```bash
# Check upload directory permissions
ls -la uploads/
chmod -R 755 uploads/

# Check container permissions
docker-compose exec economy-bot ls -la /app/static/uploads/
```

#### 5. SSL/HTTPS Issues
```bash
# Regenerate self-signed certificates
rm ssl/*
openssl req -x509 -nodes -days 365 -newkey rsa:2048 \
    -keyout ssl/key.pem -out ssl/cert.pem \
    -subj "/C=US/ST=State/L=City/O=Organization/CN=localhost"
```

### Health Checks
```bash
# Check application health
curl http://localhost:6000/

# Check container health
docker-compose ps

# Detailed health information
docker inspect economy-bot-app | grep -A 10 '"Health"'
```

### Performance Monitoring
```bash
# Monitor resource usage
docker stats economy-bot-app

# Monitor logs in real-time
docker-compose logs -f --tail=100
```

## 🌐 Production Deployment

### Domain Setup
1. Point your domain to your server IP
2. Update `DISCORD_REDIRECT_URI` in .env
3. Get proper SSL certificates (Let's Encrypt recommended)

### Let's Encrypt SSL
```bash
# Install certbot
sudo apt-get install certbot

# Get certificate
sudo certbot certonly --standalone -d your-domain.com

# Copy certificates
sudo cp /etc/letsencrypt/live/your-domain.com/fullchain.pem ssl/cert.pem
sudo cp /etc/letsencrypt/live/your-domain.com/privkey.pem ssl/key.pem
sudo chown $USER:$USER ssl/*
```

### Systemd Service (Auto-start)
```bash
# Create service file
sudo tee /etc/systemd/system/economy-bot.service > /dev/null <<EOF
[Unit]
Description=Economy Bot Docker Compose
Requires=docker.service
After=docker.service

[Service]
Type=oneshot
RemainAfterExit=true
WorkingDirectory=/path/to/Economy
ExecStart=/usr/local/bin/docker-compose --profile production up -d
ExecStop=/usr/local/bin/docker-compose down
TimeoutStartSec=0

[Install]
WantedBy=multi-user.target
EOF

# Enable and start
sudo systemctl enable economy-bot.service
sudo systemctl start economy-bot.service
```

### Backup Strategy
```bash
# Create backup script
cat > backup.sh << 'EOF'
#!/bin/bash
BACKUP_DIR="/backups/economy-bot"
DATE=$(date +%Y%m%d_%H%M%S)

mkdir -p $BACKUP_DIR

# Backup database
docker-compose exec -T economy-bot cp /app/instance/store.db /app/logs/
cp data/store.db $BACKUP_DIR/database_$DATE.db

# Backup uploads
tar -czf $BACKUP_DIR/uploads_$DATE.tar.gz uploads/

# Backup configuration
cp .env $BACKUP_DIR/env_$DATE.backup

# Clean old backups (keep 7 days)
find $BACKUP_DIR -name "*.db" -mtime +7 -delete
find $BACKUP_DIR -name "*.tar.gz" -mtime +7 -delete
find $BACKUP_DIR -name "*.backup" -mtime +7 -delete
EOF

chmod +x backup.sh

# Add to crontab (daily backup at 2 AM)
echo "0 2 * * * /path/to/Economy/backup.sh" | crontab -
```

## 📊 Monitoring and Maintenance

### Log Rotation
```bash
# Configure log rotation
sudo tee /etc/logrotate.d/economy-bot > /dev/null <<EOF
/path/to/Economy/logs/*.log {
    daily
    missingok
    rotate 30
    compress
    delaycompress
    notifempty
    postrotate
        docker-compose exec economy-bot pkill -USR1 -f "python app.py"
    endscript
}
EOF
```

### Updates
```bash
# Update application
git pull
docker-compose build --no-cache
docker-compose down
docker-compose up -d

# Update base images
docker-compose pull
docker-compose up -d
```

## 🆘 Support

If you encounter issues:

1. Check the logs: `docker-compose logs -f`
2. Verify configuration: `.env` file settings
3. Test Discord bot permissions
4. Check network connectivity
5. Review the troubleshooting section above

For additional help, check the main `DIGITAL_PRODUCTS_GUIDE.md` file for application-specific features and usage. 