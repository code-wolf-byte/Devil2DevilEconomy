# Discord Store Front

A Flask-based store front that integrates with a Discord economy bot, allowing users to spend their earned points on various products.

## Features

- View all available products in the store
- Detailed product pages with purchase functionality
- Admin panel for managing products
- Discord bot integration for point management
- User authentication with Discord
- Modern, responsive UI using Tailwind CSS

## Prerequisites

- Python 3.8 or higher
- Discord Bot Token
- Flask
- SQLAlchemy
- discord.py

## Setup

1. Clone the repository:
```bash
git clone <repository-url>
cd discord-store
```

2. Create a virtual environment and activate it:
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. Install the required packages:
```bash
pip install -r requirements.txt
```

4. Set up environment variables:
   - Copy `env.example` to `.env`
   - Fill in the required variables:
     - `DISCORD_TOKEN`: Your Discord bot token from the Discord Developer Portal
     - `SECRET_KEY`: A secure secret key for Flask (you can generate one using the command in the example file)
   - Optional variables:
     - Database configuration if you want to use PostgreSQL or MySQL
     - Application settings for development/production
     - Discord bot settings for customization

5. Initialize the database:
```bash
flask db init
flask db migrate
flask db upgrade
```

6. Run the application:
```bash
python app.py
```

## Environment Variables

### Required Variables
- `DISCORD_TOKEN`: Your Discord bot token from the Discord Developer Portal
- `SECRET_KEY`: A secure secret key for Flask session management

### Optional Variables
- `DATABASE_URL`: Database connection URL (defaults to SQLite)
- `FLASK_ENV`: Set to 'development' or 'production'
- `FLASK_DEBUG`: Set to 1 for development, 0 for production
- `HOST`: Application host (default: 0.0.0.0)
- `PORT`: Application port (default: 5000)
- `BOT_PREFIX`: Discord bot command prefix (default: !)
- `ADMIN_ROLE_ID`: Discord role ID for admin commands

## Discord Bot Commands

- `!points` - Check your current point balance
- `!addpoints @user amount` - Add points to a user (Admin only)

## Admin Features

1. Access the admin panel at `/admin`
2. Add new products with:
   - Name
   - Description
   - Price (in points)
   - Stock quantity
   - Image URL
3. Edit existing products
4. Delete products
5. Monitor user purchases

## Contributing

1. Fork the repository
2. Create a new branch
3. Make your changes
4. Submit a pull request

## License

This project is licensed under the MIT License - see the LICENSE file for details. 