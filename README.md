# Devil2Devil Store 🏪

A professional Discord economy bot and web application built with Flask and Nextcord, featuring a modern ASU-themed UI, custom emoji reward system, and comprehensive shop management.

## 🧪 Economy System Testing Checklist

Before deploying the economy system, perform these tests to ensure everything works as intended:

### 🔧 **Initial Setup Tests**

#### ✅ **Bot Startup & Connection**
- [ ] Bot starts without errors
- [ ] Bot connects to Discord successfully
- [ ] Bot shows as online in Discord server
- [ ] Slash commands sync properly (`/balance`, `/daily`, etc. appear in Discord)
- [ ] Web application starts on correct port (default: 5000)
- [ ] Database migrations run successfully

#### ✅ **Environment Configuration**
- [ ] All required environment variables are set in `.env`
- [ ] Discord bot token is valid
- [ ] Discord OAuth credentials work
- [ ] Channel IDs are correct (GENERAL_CHANNEL_ID, etc.)
- [ ] Role IDs are correct (VERIFIED_ROLE_ID, ONBOARDING_ROLE_IDS)

### 💰 **Basic Economy Commands**

#### ✅ **Balance Command** (`/balance`)
- [ ] New users get default balance (0 points)
- [ ] Balance displays correctly for existing users
- [ ] Command works in DMs and server channels
- [ ] Embed formatting displays properly

#### ✅ **Daily Reward** (`/daily`)
- [ ] First-time users can claim 85 points
- [ ] Balance increases by 85 points after claiming
- [ ] 24-hour cooldown prevents multiple claims
- [ ] Cooldown timer shows remaining time accurately
- [ ] Error message displays when economy is disabled

#### ✅ **Leaderboard** (`/leaderboard`)
- [ ] Shows top 10 users by balance
- [ ] Users are ranked correctly (highest to lowest)
- [ ] Displays "No users found" when database is empty
- [ ] Updates in real-time as balances change

### 🏆 **Achievement System**

#### ✅ **Achievement Tracking**
- [ ] Message count increases when users send messages
- [ ] Reaction count increases when users react to messages
- [ ] Voice minutes track when users join voice channels
- [ ] Achievement requirements are checked correctly

#### ✅ **Achievement Awards**
- [ ] Users receive achievements when meeting requirements
- [ ] Points are awarded correctly for achievements
- [ ] Achievement announcements appear in general channel
- [ ] Users can't receive the same achievement twice
- [ ] `/achievements` command shows user's unlocked achievements

### 👑 **Admin Functions**

#### ✅ **Economy Toggle** (`/economy`)
- [ ] Only administrators can use the command
- [ ] `/economy enable` activates the economy system
- [ ] `/economy disable` deactivates the economy system
- [ ] First-time enable awards "Verified" achievement to verified users
- [ ] Commands are disabled when economy is off

#### ✅ **Bulk Point Distribution** (`/give_all`)
- [ ] Only administrators can use the command
- [ ] Points are added to all users' balances
- [ ] Database updates correctly for all users
- [ ] No users are missed in the distribution

### 🎯 **Point Earning Methods**

#### ✅ **Role-Based Bonuses**
- [ ] Verification bonus (200 points) awarded when user gets verified role
- [ ] Onboarding bonus (500 points) awarded for onboarding roles
- [ ] Bonuses are only awarded once per user
- [ ] Welcome messages appear in general channel
- [ ] Atomic transactions prevent duplicate bonuses

#### ✅ **Custom Emoji Rewards**
- [ ] Admin reactions with `:daily_engage:` award 25 points
- [ ] Admin reactions with `:campus_photo:` award 100 points (only on image posts)
- [ ] Admin reactions with `:deposit_check:` award 500 points (one-time)
- [ ] Non-admin reactions don't award points
- [ ] Cooldowns work correctly (20 hours for daily engagement)
- [ ] Confirmation messages are sent to users

#### ✅ **Activity Tracking**
- [ ] Message count increases when users post messages
- [ ] Reaction count increases when users react
- [ ] Voice time tracks when users join voice channels
- [ ] Only human users are tracked (bots ignored)

### 🎂 **Birthday System**

#### ✅ **Birthday Registration**
- [ ] Users can set birthday with `/birthday` command
- [ ] Birthday can only be set once per user
- [ ] 50 points awarded for setting birthday
- [ ] Invalid dates are rejected

#### ✅ **Birthday Announcements**
- [ ] Daily birthday check runs at 9:30 MST
- [ ] Birthday announcements appear in general channel
- [ ] Correct users are announced on their birthday
- [ ] No announcements when no birthdays

### 🌐 **Web Interface Tests**

#### ✅ **Authentication**
- [ ] Discord OAuth login works
- [ ] Users are redirected correctly after login
- [ ] User sessions persist correctly
- [ ] Logout functionality works

#### ✅ **Store Functionality**
- [ ] Products display correctly on homepage
- [ ] Purchase confirmation dialog appears
- [ ] Purchases deduct correct points from balance
- [ ] Purchase history shows in "My Purchases" page
- [ ] Stock levels update after purchases

#### ✅ **Admin Panel**
- [ ] Only admins can access admin routes
- [ ] Product management (add/edit/delete) works
- [ ] Image uploads function properly
- [ ] Purchase history displays correctly
- [ ] User management features work

### 🔄 **Background Tasks**

#### ✅ **Role Assignment Processor**
- [ ] Digital product role assignments process correctly
- [ ] Failed assignments are marked appropriately
- [ ] Users receive confirmation DMs when roles are assigned
- [ ] Task runs every 30 seconds without errors

#### ✅ **Birthday Check Task**
- [ ] Task starts automatically when bot starts
- [ ] Runs daily at configured time (9:30 MST)
- [ ] Handles timezone conversion correctly
- [ ] Doesn't crash on database errors

### 🛡️ **Error Handling & Edge Cases**

#### ✅ **Database Integrity**
- [ ] Concurrent transactions don't cause race conditions
- [ ] Database rollbacks work on errors
- [ ] User creation handles duplicates gracefully
- [ ] Foreign key constraints are respected

#### ✅ **Discord API Limits**
- [ ] Rate limiting is handled properly
- [ ] Failed DMs fall back to channel messages
- [ ] Bot handles missing permissions gracefully
- [ ] Large embed messages don't exceed Discord limits

#### ✅ **Input Validation**
- [ ] Invalid command parameters are rejected
- [ ] SQL injection attempts are prevented
- [ ] File uploads are validated properly
- [ ] User input is sanitized

### 📊 **Performance Tests**

#### ✅ **Load Testing**
- [ ] Bot handles multiple simultaneous commands
- [ ] Web interface responds quickly under load
- [ ] Database queries are optimized
- [ ] Memory usage remains stable over time

#### ✅ **Data Consistency**
- [ ] Point balances match transaction history
- [ ] Achievement counts are accurate
- [ ] Purchase records are complete
- [ ] User statistics are correct

### 🔍 **Final Verification**

#### ✅ **End-to-End User Journey**
- [ ] New user joins server → gets roles → receives bonuses
- [ ] User earns points through various methods
- [ ] User makes purchases → balance decreases → purchase recorded
- [ ] User unlocks achievements → receives points → announcement sent
- [ ] Admin manages economy → changes take effect immediately

#### ✅ **System Health**
- [ ] No memory leaks after extended operation
- [ ] Log files don't show recurring errors
- [ ] All background tasks continue running
- [ ] Database performance remains stable

---

### 🚨 **Critical Issues to Watch For**

- **Duplicate Bonuses**: Users receiving verification/onboarding bonuses multiple times
- **Race Conditions**: Multiple transactions modifying the same user's balance simultaneously
- **Achievement Spam**: Users receiving the same achievement repeatedly
- **Command Failures**: Slash commands not responding or showing errors
- **Database Locks**: Long-running transactions blocking other operations
- **Memory Leaks**: Bot memory usage increasing over time
- **Task Failures**: Background tasks stopping unexpectedly

### 📝 **Testing Notes**

- Test with multiple users to verify concurrent operations
- Use different Discord clients (desktop, mobile, web) to ensure compatibility
- Test during peak usage times to identify performance issues
- Monitor logs during testing for any warnings or errors
- Verify all features work when economy is disabled and re-enabled

---

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