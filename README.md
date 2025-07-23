# D2D Economy

A comprehensive Discord economy system with web interface, achievements, and digital product delivery. Similar to the [Devil2DevilEconomy](https://github.com/code-wolf-byte/Devil2DevilEconomy) project.

## 🚀 Features

### Discord Integration
- **OAuth Authentication**: Login with Discord account
- **Slash Commands**: `/balance`, `/daily`, `/leaderboard`, `/achievements`
- **Reaction System**: Earn points through emoji reactions
- **Voice Activity**: Points for spending time in voice channels
- **Message Tracking**: Points for sending messages and reactions

### Web Interface
- **Modern UI**: Beautiful, responsive design with Tailwind CSS
- **User Dashboard**: View balance, achievements, and recent purchases
- **Shop System**: Browse and purchase products with points
- **Admin Panel**: Manage products, users, and economy settings
- **Leaderboard**: See top users by point balance

### Achievement System
- **Automatic Unlocking**: Achievements based on user activity
- **Point Rewards**: Bonus points for completing achievements
- **Announcements**: Automatic Discord announcements for achievements

### Digital Products
- **Discord Roles**: Automatic role assignment
- **Minecraft Skins**: Download system for custom skins
- **Game Codes**: Digital code delivery
- **Physical Products**: Support for real-world items

## 🛠️ Installation

### Prerequisites
- Python 3.8+
- Discord Bot Token
- Discord OAuth Application
- SQLite (included) or PostgreSQL

### 1. Clone the Repository
```bash
git clone <your-repo-url>
cd D2D-Economy
```

### 2. Set Up Virtual Environment
```bash
python -m venv env
source env/bin/activate  # On Windows: env\Scripts\activate
```

### 3. Install Dependencies
```bash
pip install -r requirements.txt
```

### 4. Environment Configuration
Copy the example environment file and configure it:
```bash
cp .env.example .env
```

Edit `.env` with your Discord credentials:
```env
# Discord Bot Configuration
DISCORD_TOKEN=your_discord_bot_token_here
DISCORD_CLIENT_ID=your_discord_client_id_here
DISCORD_CLIENT_SECRET=your_discord_client_secret_here
DISCORD_REDIRECT_URI=http://localhost:6000/callback

# Discord Server Configuration
GENERAL_CHANNEL_ID=your_general_channel_id_here
GUILD_ID=your_discord_server_id_here
VERIFIED_ROLE_ID=your_verified_role_id_here
ONBOARDING_ROLE_IDS=role_id_1,role_id_2,role_id_3

# Role Management Configuration
UNVERIFIED_ROLE_NAME=Unverified
COMMITTED_ROLE_NAME=Committed

# Flask Configuration
SECRET_KEY=your_secret_key_here
FLASK_ENV=development
DATABASE_URL=sqlite:///store.db

# Point System Configuration
DAILY_ENGAGEMENT_POINTS=25
CAMPUS_PICTURE_POINTS=100
ENROLLMENT_DEPOSIT_POINTS=500
BIRTHDAY_SETUP_POINTS=50
DAILY_POINTS=85

# Emoji Configuration
CAMPUS_PICTURE_EMOJI=campus_photo
DAILY_ENGAGEMENT_EMOJI=daily_engage
ENROLLMENT_DEPOSIT_EMOJI=deposit_check

# Birthday System
BIRTHDAY_CHECK_TIME=09:30

# File Upload Configuration
UPLOAD_FOLDER=static/uploads
MAX_CONTENT_LENGTH=16777216
```

### 5. Discord Bot Setup

1. **Create Discord Application** at [Discord Developer Portal](https://discord.com/developers/applications)
2. **Create Bot** and get token
3. **Set OAuth Redirects** to match your domain
4. **Bot Permissions** needed:
   - Send Messages
   - Read Message History
   - Add Reactions
   - Use Slash Commands
   - Embed Links
   - Manage Roles (for role assignments)

### 6. Run the Application
```bash
python main.py
```

The web interface will be available at `http://localhost:6000`

## 🛡️ Role Management System

The bot includes an automatic role management system that prevents unverified users from having access to committed member roles.

### How It Works
- **Unverified Role**: Users with this role are considered unverified
- **Committed Role**: A restricted role that unverified users cannot have
- **Automatic Enforcement**: The bot automatically removes the committed role from anyone with the unverified role
- **Real-time Monitoring**: Role changes are monitored in real-time to enforce restrictions

### Configuration
Set these environment variables to configure role names:
```env
UNVERIFIED_ROLE_NAME=Unverified
COMMITTED_ROLE_NAME=Committed
```

### Admin Commands for Role Management
- `/remove_restricted_roles` - Bulk remove committed role from all unverified users

## 🎮 Discord Commands

### User Commands
- `/balance` - Check your current point balance
- `/daily` - Claim your daily 85 point reward
- `/birthday <month> <day>` - Set your birthday (earn 50 points)
- `/leaderboard` - View top 10 users by balance
- `/achievements` - View your earned achievements
- `/qrcode` - Get your unique QR code (requires purchase)

### Admin Commands
- `/give_all <amount>` - Give points to all users
- `/emoji_system` - View emoji reward system information
- `/remove_restricted_roles` - Remove committed role from unverified users

## 🌐 Web Features

### User Features
- **Dashboard**: View balance, points earned, and purchases
- **Shop**: Browse and purchase products
- **Responsive Design**: Works on mobile and desktop
- **Discord Integration**: Login with Discord OAuth

### Admin Features
- **Product Management**: Add, edit, delete products
- **Image Upload**: Product images with validation
- **Stock Management**: Set limited or unlimited stock
- **Purchase Analytics**: View all purchases with pagination
- **User Management**: View user statistics

## 🎨 Customization

### Theming
The application uses ASU colors but can be customized in `templates/base.html`:
```css
:root {
    --asu-maroon: #8C1D40;
    --asu-gold: #FFC627;
    --dark-bg: #1a1a1a;
    --dark-card: #2d2d2d;
}
```

### Point Values
Easily adjust point rewards in the environment variables:
```env
DAILY_ENGAGEMENT_POINTS=25
CAMPUS_PICTURE_POINTS=100
ENROLLMENT_DEPOSIT_POINTS=500
BIRTHDAY_SETUP_POINTS=50
```

## 📊 Database Schema

### User Model
- `id` (Discord ID)
- `username`
- `discord_id`
- `avatar_url`
- `user_uuid` (generated on first purchase)
- `is_admin`
- `points` (total earned)
- `balance` (available to spend)
- `last_daily`
- `last_daily_engagement`
- `enrollment_deposit_received`
- `birthday` (date field)
- `birthday_points_received` (boolean)
- `message_count`, `reaction_count`, `voice_minutes`
- `achievement` relationships

### Product Model
- `id`
- `name`
- `description`
- `price`
- `stock` (0 = unlimited)
- `image_url`
- `created_at`
- `product_type` (physical, role, minecraft_skin, game_code, custom)
- `delivery_method`
- `delivery_data` (JSON for delivery configuration)

### Purchase Model
- `id`
- `user_id`
- `product_id`
- `points_spent`
- `timestamp`
- `delivery_info`
- `status`

## 🚦 Deployment

### Production Setup
1. Set `FLASK_ENV=production`
2. Use PostgreSQL instead of SQLite
3. Configure reverse proxy (nginx)
4. Set up SSL certificates
5. Use process manager (systemd/supervisor)

### Environment Variables for Production
```env
DATABASE_URL=postgresql://user:pass@host:port/dbname
FLASK_ENV=production
DISCORD_REDIRECT_URI=https://yourdomain.com/callback
```

## 🤝 Contributing

1. Fork the repository
2. Create feature branch (`git checkout -b feature/amazing-feature`)
3. Commit changes (`git commit -m 'Add amazing feature'`)
4. Push to branch (`git push origin feature/amazing-feature`)
5. Open Pull Request

## 📄 License

This project is licensed under the MIT License - see the LICENSE file for details.

## 🆘 Support

For support and questions:
1. Check the `/emoji_system` command for current settings
2. Review bot logs for error messages
3. Verify Discord permissions and OAuth settings
4. Check database connectivity

## 🎯 Roadmap

- Enhanced achievement system
- User profile customization
- Product categories and filtering
- Advanced analytics dashboard
- Mobile app integration
- Multi-server support

## 📋 TODO - Next Development Cycle

### 🔧 Database Maintenance Tasks
- [ ] **Remove deprecated `models.py` file** - All models have been moved to `shared.py`, the legacy file should be deleted
- [ ] **Database migration to PostgreSQL** - Current SQLite setup needs upgrade for production scalability  
- [ ] **Automated balance consistency monitoring** - Currently runs on startup but could benefit from periodic health checks
- [ ] **Clean up image path inconsistencies** - Some products still have `/static/uploads/` prefixes that need ongoing monitoring
- [ ] **Review download token expiration logic** - 30-day expiration may need adjustment based on usage patterns

### 🐳 Docker & Deployment Improvements  
- [ ] **Implement proper user mapping** - Currently using root container approach, should migrate to proper UID/GID mapping
- [ ] **Automate backup retention policy** - `deploy.sh` creates timestamped backups but no cleanup mechanism
- [ ] **Container health checks** - Add proper Docker health check endpoints beyond basic connectivity tests
- [ ] **Permission persistence testing** - Ensure file permissions survive container restarts and updates
- [ ] **Multi-stage Docker build optimization** - Current Dockerfile could be optimized for smaller image size

### 🧹 Code Cleanup & Refactoring
- [ ] **Requirements.txt cleanup** - Remove all commented packages and unused dependencies 
- [ ] **Consolidate startup checks** - Multiple permission/database checks in `main.py` could be modularized
- [ ] **Remove hardcoded paths** - Several scripts have hardcoded `/app/` paths that should be configurable
- [ ] **Centralize file upload logic** - Upload handling is scattered across multiple routes
- [ ] **Abstract permission management** - File permission logic is duplicated in `deploy.sh` and `main.py`

### 🗂️ File System Organization
- [ ] **Implement upload file cleanup job** - No mechanism for cleaning old/unused uploaded files
- [ ] **Standardize directory structure** - Mix of `uploads/` and `static/uploads/` directories needs consolidation
- [ ] **Add file size monitoring** - No alerts for when upload directories grow too large
- [ ] **Create staging environment** - All testing currently done on production data

### 🚦 Testing & Monitoring
- [ ] **Expand `test_bot_connection.py`** - Current test is basic, needs comprehensive Discord API testing
- [ ] **Add database integrity checks** - Beyond balance consistency, need referential integrity validation
- [ ] **Container resource monitoring** - No monitoring of memory/CPU usage within containers
- [ ] **Implement logging rotation** - Application logs could grow indefinitely
- [ ] **Add performance benchmarking** - No baseline metrics for response times or throughput

### 🔐 Security & Compliance  
- [ ] **Audit file permissions strategy** - Current 777/666 permissions are overly permissive
- [ ] **Review Discord token security** - Ensure proper token rotation procedures are documented
- [ ] **Implement rate limiting** - No protection against API abuse on web endpoints
- [ ] **Add input validation audit** - File upload and form inputs need security review
- [ ] **Environment variable validation** - Missing .env variables fail silently

### 📊 Data Management
- [ ] **Implement data export functionality** - No easy way to export user/purchase data
- [ ] **Add database schema versioning** - Current migrations lack proper version control
- [ ] **Create data anonymization scripts** - For GDPR compliance and testing
- [ ] **Establish backup verification process** - Backups created but never tested for restoration
- [ ] **Plan for data archival** - Old purchases and inactive users should be archived

### 🎯 Priority Items (Next Sprint)
1. **Remove deprecated `models.py`** (Low risk, quick win)
2. **Clean up `requirements.txt`** (Reduces Docker build time)  
3. **Consolidate upload directories** (Fixes user confusion)
4. **Add container health checks** (Production stability)
5. **Implement proper Docker user mapping** (Security improvement)

### 💡 Notes for Maintainers
- Many tasks marked with 🔧 in startup logs indicate technical debt
- `deploy.sh` script contains significant deployment logic that should be CI/CD automated
- Permission fixes appear in multiple places indicating a systematic issue
- Testing currently requires manual setup - automation needed

---

**Made with ❤️ for Discord communities seeking engaging economy systems.** 