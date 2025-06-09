# Devil2Devil Store 🏪

A professional Discord economy bot and web application built with Flask and Nextcord, featuring a modern ASU-themed UI, custom emoji reward system, and comprehensive shop management.

## 🌟 Features

### 🎮 Discord Bot Integration
- **Slash Commands** for user interaction
- **Custom Emoji Reward System** with admin approval
- **Real-time Point Tracking** across Discord and web
- **Achievement System** with automated rewards
- **QR Code Generation** for unique user identification

### 🌐 Modern Web Interface
- **Professional ASU-themed Design** (Maroon & Gold)
- **Responsive Mobile-First Layout** 
- **Smooth Animations** and modern UI components
- **Discord OAuth Authentication**
- **Admin Management Panel**
- **Purchase History Tracking**

### 🛒 Shop Management
- **Product Management** with image uploads
- **Stock Management** (limited or unlimited)
- **Purchase System** with balance validation
- **Admin Analytics** and purchase history

### 🏆 Point System
- **Multiple Earning Methods** (see below)
- **Balance Tracking** separate from total points earned
- **Purchase Integration** with automatic deductions
- **Admin Point Distribution** tools

### 🎮 Economy System
- **Enable/Disable Economy**: Admin command to control the entire economy system
- **First-Time Setup**: Automatically awards existing verified members when economy is first enabled
- **Points and Balance**: Dual currency system for earning and spending
- **Daily Rewards**: 85 points daily with 24-hour cooldown
- **Achievement System**: Automated achievements for various milestones
- **Leaderboards**: Real-time rankings by balance

### 🏪 Store Integration
- **Product Management**: Admin can add/edit/delete products with images
- **Stock Control**: Limited and unlimited stock options
- **Purchase History**: Track all user purchases
- **QR Code Generation**: Secure purchase verification system

### 🎯 Point Earning Methods
- **Verification Bonus**: 200 points for getting verified role (one-time)
- **Onboarding Bonus**: 500 points for completing onboarding (one-time)
- **Custom Emoji Rewards**: Admin-controlled point awards via reactions
  - Campus Picture Posts: 100 points (react to posts with images)
  - Daily Engagement: 25 points (20-hour cooldown)
  - Enrollment Deposit: 500 points (one-time bonus)
- **Birthday Setup**: 50 points for setting birthday once
- **Achievements**: Various point rewards for milestones

### 🎂 Birthday System
- **Birthday Registration**: Users can set their birthday once for points
- **Daily Announcements**: Automated birthday celebrations at 9:30 MST
- **Community Engagement**: Public birthday announcements in general channel

### 👑 Admin Features
- **Economy Toggle**: Enable/disable the entire economy system
- **Role-Based Automation**: Automatic point awards for role assignments
- **Custom Emoji System**: Award points via emoji reactions
- **Product Management**: Full CRUD operations for store items
- **Purchase Tracking**: Monitor all transactions and user activity
- **Bulk Operations**: Give points to all users simultaneously

## 💰 How Users Can Earn Points

### 🔄 Regular Activities

#### 1. **Daily Reward** `/daily` - 85 Points
- **Frequency**: Once every 24 hours
- **Method**: Use `/daily` command in Discord
- **Automatic**: No admin approval needed

#### 2. **Daily Engagement** - 25 Points ⭐
- **Frequency**: Once every 20 hours  
- **Method**: Post any message in Discord
- **Requirement**: Admin reacts with `:daily_engage:` custom emoji
- **Admin Action Required**: Yes

#### 3. **Campus Picture Posts** - 100 Points 📸
- **Frequency**: No limit
- **Method**: Post a message with image attachments
- **Requirement**: Admin reacts with `:campus_photo:` custom emoji
- **Validation**: Message must contain images
- **Admin Action Required**: Yes

#### 4. **Enrollment Deposit** - 500 Points 💰
- **Frequency**: One-time bonus per user
- **Method**: Post about enrollment deposit submission
- **Requirement**: Admin reacts with `:deposit_check:` custom emoji
- **Admin Action Required**: Yes

#### 5. **Birthday Setup** - 50 Points 🎂
- **Frequency**: One-time bonus per user
- **Method**: Use `/birthday <month> <day>` command in Discord
- **Automatic**: No admin approval needed
- **Bonus**: Daily birthday announcements in #general channel

### 🏆 Achievement System

Users earn points automatically when reaching milestones:

- **Message Milestones**: Points for sending messages
- **Reaction Milestones**: Points for reacting to messages  
- **Voice Activity**: Points for spending time in voice channels
- **Server Boosting**: Bonus points for boosting the server
- **Community Participation**: Various engagement achievements

**🎉 Achievement Announcements**: When users unlock achievements, the bot automatically posts a celebration message in the #general channel with:
- User ping and congratulations
- Achievement name and description
- Points earned from the achievement
- User's new point balance

### 👑 Admin Tools

Administrators can award points using:
- **Bulk Point Distribution**: Give points to all users at once
- **Custom Emoji Reactions**: Approve activities for point rewards
- **Manual Balance Adjustments**: Direct point management

## 🚀 Quick Start

### Prerequisites

- Python 3.8+
- Discord Bot Token
- Discord OAuth Application
- SQLite (included) or PostgreSQL

### Installation

1. **Clone the Repository**
```bash
git clone <repository-url>
cd Economy
```

2. **Install Dependencies**
```bash
pip install -r requirements.txt
```

3. **Environment Setup**
Create a `.env` file:
```env
DISCORD_TOKEN=your_discord_bot_token_here
DISCORD_CLIENT_ID=your_discord_client_id_here
DISCORD_CLIENT_SECRET=your_discord_client_secret_here
DISCORD_REDIRECT_URI=http://localhost:5000/callback
GENERAL_CHANNEL_ID=your_general_channel_id_here
SECRET_KEY=your_secret_key_here
DATABASE_URL=sqlite:///store.db
GUILD_ID=your_discord_server_id_here
VERIFIED_ROLE_ID=your_verified_role_id_here
ONBOARDING_ROLE_IDS=role_id_1,role_id_2,role_id_3
```

4. **Run the Application**
```bash
python app.py
```

The web interface will be available at `http://localhost:5000`

## ⚙️ Configuration

### Custom Emoji Setup

1. **Upload Custom Emojis** to your Discord server with these names:
   - `:daily_engage:` - For daily engagement approval
   - `:campus_photo:` - For campus picture approval  
   - `:deposit_check:` - For enrollment deposit approval

2. **Update Bot Configuration** in `bot.py`:
```python
CAMPUS_PICTURE_EMOJI = "campus_photo"        # Your custom emoji name
DAILY_ENGAGEMENT_EMOJI = "daily_engage"      # Your custom emoji name  
ENROLLMENT_DEPOSIT_EMOJI = "deposit_check"   # Your custom emoji name
```

3. **Adjust Point Values**:
```python
DAILY_ENGAGEMENT_POINTS = 25   # Points for daily engagement
CAMPUS_PICTURE_POINTS = 100    # Points for campus pictures
ENROLLMENT_DEPOSIT_POINTS = 500 # Points for enrollment deposit
```

### Discord Bot Setup

1. **Create Discord Application** at https://discord.com/developers/applications
2. **Create Bot** and get token
3. **Set OAuth Redirects** to match your domain
4. **Bot Permissions** needed:
   - Send Messages
   - Read Message History
   - Add Reactions
   - Use Slash Commands
   - Embed Links

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

## 🛠️ Technical Stack

### Backend
- **Flask** - Web framework
- **SQLAlchemy** - Database ORM
- **Flask-Login** - User session management
- **Nextcord** - Discord bot library
- **Werkzeug** - File upload handling

### Frontend
- **Tailwind CSS** - Utility-first CSS framework
- **Font Awesome** - Icon library
- **Custom CSS** - Animations and ASU theming
- **Responsive Design** - Mobile-first approach

### Database Schema
- **Users**: Discord integration, points, achievements
- **Products**: Shop items with images and stock
- **Purchases**: Transaction history with timestamps
- **Achievements**: Milestone tracking system

## 📊 Database Models

### User Model
```python
- id (Discord ID)
- username
- discord_id
- avatar_url
- user_uuid (generated on first purchase)
- is_admin
- points (total earned)
- balance (available to spend)
- last_daily
- last_daily_engagement
- enrollment_deposit_received
- birthday (date field)
- birthday_points_received (boolean)
- message_count, reaction_count, voice_minutes
- achievement relationships
```

### Product Model
```python
- id
- name
- description  
- price
- stock (0 = unlimited)
- image_url
- created_at
```

### Purchase Model
```python
- id
- user_id
- product_id
- points_spent
- timestamp
```

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
Easily adjust point rewards in `bot.py`:
```python
DAILY_ENGAGEMENT_POINTS = 25
CAMPUS_PICTURE_POINTS = 100  
ENROLLMENT_DEPOSIT_POINTS = 500
BIRTHDAY_SETUP_POINTS = 50
```

### Birthday System
The bot automatically checks for birthdays daily at 9:30 MST and sends announcements to the general channel:
```python
GENERAL_CHANNEL_ID = "your_general_channel_id"  # Set in environment variables
BIRTHDAY_CHECK_TIME = "09:30"  # MST timezone
```

### Achievement Announcements  
All achievements are automatically announced in the general channel with beautiful embeds that include user pings, achievement details, and point rewards. This encourages community engagement and celebrates user milestones.

## 🔒 Security Features

- **OAuth Authentication** with Discord
- **Admin Permission Validation**
- **File Upload Security** with type validation
- **SQL Injection Protection** via SQLAlchemy ORM
- **Session Management** with secure cookies

## 📱 Mobile Experience

- **Touch-Friendly** buttons (44px minimum)
- **Responsive Grid** layouts
- **Mobile Navigation** optimizations
- **Fast Loading** with optimized assets
- **Progressive Enhancement**

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

## 📈 Analytics & Monitoring

### Available Metrics
- **User Engagement**: Message counts, reaction counts
- **Purchase Analytics**: Revenue, popular products
- **Achievement Progress**: User milestone tracking
- **Admin Activity**: Point distribution tracking

### Admin Dashboard Features
- **User Statistics**: Total users, active users
- **Sales Analytics**: Purchase history with pagination
- **Stock Monitoring**: Product availability tracking
- **Point Economy**: Total points in circulation

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

- [ ] Enhanced achievement system
- [ ] User profile customization
- [ ] Product categories and filtering
- [ ] Advanced analytics dashboard
- [ ] Mobile app integration
- [ ] Multi-server support

---

**Made with ❤️ for Discord communities seeking engaging economy systems.** 