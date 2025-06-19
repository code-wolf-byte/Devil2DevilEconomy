# 🚀 Quick Start Guide

## One-Command Setup

Simply run:

```bash
python app.py
```

That's it! The application will automatically:
- ✅ Install missing dependencies
- ✅ Create necessary directories
- ✅ Set up the database
- ✅ Create a default `.env` file
- ✅ Start the web interface

## First Time Setup

1. **Run the application**: `python app.py`
2. **Edit configuration**: Open the generated `.env` file and add your Discord bot credentials
3. **Restart**: Run `python app.py` again

## Getting Discord Credentials

1. Go to [Discord Developer Portal](https://discord.com/developers/applications)
2. Create a new application
3. Go to the **Bot** section and create a bot
4. Copy the **Token** → paste in `DISCORD_TOKEN`
5. Go to **OAuth2** section:
   - Copy **Client ID** → paste in `DISCORD_CLIENT_ID`
   - Copy **Client Secret** → paste in `DISCORD_CLIENT_SECRET`

## What You Get

- **Web Interface**: http://localhost:6000
- **Admin Panel**: Login with Discord to access admin features
- **Discord Bot**: Economy system with slash commands
- **Database**: Automatically created SQLite database

## Web-Only Mode

The application works without Discord configuration! You'll get:
- ✅ Web interface for managing products
- ✅ User authentication via Discord OAuth
- ❌ Discord bot features (commands, reactions, etc.)

Configure Discord later to enable full functionality.

## Troubleshooting

**"Module not found"**: The app automatically installs dependencies, but you might need to run `pip install -r requirements.txt` manually in some environments.

**"Permission denied"**: Make sure you have write permissions in the current directory.

**"Port already in use"**: Another application is using port 6000. Stop it or modify the port in `app.py`.

---

For detailed documentation, see `README.md` 